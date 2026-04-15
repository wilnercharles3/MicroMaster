// Web Worker that hosts the Pyodide runtime.
//
// Module worker (ES module). We import Pyodide's ESM entry point via
// dynamic import from the CDN. Pyodide's own code uses relative paths
// inside its indexURL to find the Python stdlib and wasm payload.
//
// One worker instance is shared across the whole app (see client.ts).
// Running code inside a worker keeps a heavy Python call from freezing
// the UI, and if a user writes an infinite loop we can terminate the
// worker and spin up a new one.

/// <reference lib="webworker" />

import type {
  LoadingProgress,
  ReadyMessage,
  ResetResult,
  RunResult,
  StatusMessage,
  StdoutMessage,
  WorkerInbound,
  WorkerOutbound,
} from './types'

declare const self: DedicatedWorkerGlobalScope

const PYODIDE_VERSION = '0.26.4'
const PYODIDE_BASE = `https://cdn.jsdelivr.net/pyodide/v${PYODIDE_VERSION}/full/`

interface PyodideInterface {
  runPythonAsync: (code: string) => Promise<unknown>
  setStdout: (opts: { batched: (msg: string) => void }) => void
  setStderr: (opts: { batched: (msg: string) => void }) => void
  globals: { clear: () => void; get: (k: string) => unknown; set: (k: string, v: unknown) => void }
}

let pyodide: PyodideInterface | null = null
let status: StatusMessage['status'] = 'idle'
let activeRunId: string | null = null

function post(msg: WorkerOutbound): void {
  self.postMessage(msg)
}

function setStatus(next: StatusMessage['status']): void {
  status = next
  post({ type: 'status', status })
}

async function bootPyodide(): Promise<void> {
  setStatus('loading')
  post({
    type: 'loading-progress',
    stage: 'boot',
    message: 'Fetching Pyodide loader...',
  } satisfies LoadingProgress)

  // Use the ESM build so this works inside a Vite-bundled module worker
  // without any importScripts dance.
  const mod = await import(/* @vite-ignore */ `${PYODIDE_BASE}pyodide.mjs`)
  const loadPyodide = mod.loadPyodide as (opts: { indexURL: string }) => Promise<PyodideInterface>

  post({
    type: 'loading-progress',
    stage: 'pyodide',
    message: 'Booting Python runtime (one-time, ~10 MB)...',
  })

  pyodide = await loadPyodide({ indexURL: PYODIDE_BASE })
  if (!pyodide) throw new Error('loadPyodide returned nothing')

  // Pyodide's batched stdout/stderr handler emits a chunk each time a
  // newline is flushed but passes the text without the trailing \n.
  // Re-add it so multiple print() calls appear on separate lines.
  pyodide.setStdout({
    batched: (text: string) => {
      if (!activeRunId) return
      post({ type: 'stdout', id: activeRunId, text: text + '\n', stream: 'stdout' } satisfies StdoutMessage)
    },
  })
  pyodide.setStderr({
    batched: (text: string) => {
      if (!activeRunId) return
      post({ type: 'stdout', id: activeRunId, text: text + '\n', stream: 'stderr' } satisfies StdoutMessage)
    },
  })

  setStatus('ready')
  post({ type: 'ready', version: PYODIDE_VERSION } satisfies ReadyMessage)
}

async function runCode(id: string, code: string): Promise<void> {
  if (!pyodide) {
    post({
      type: 'run-result',
      id,
      success: false,
      stdout: '',
      stderr: '',
      result: null,
      error: { name: 'NotReady', message: 'Pyodide is still loading', trace: '' },
      elapsedMs: 0,
    } satisfies RunResult)
    return
  }

  setStatus('running')
  activeRunId = id
  const stdoutBuf: string[] = []
  const stderrBuf: string[] = []

  pyodide.setStdout({
    batched: (text: string) => {
      const line = text + '\n'
      stdoutBuf.push(line)
      post({ type: 'stdout', id, text: line, stream: 'stdout' })
    },
  })
  pyodide.setStderr({
    batched: (text: string) => {
      const line = text + '\n'
      stderrBuf.push(line)
      post({ type: 'stdout', id, text: line, stream: 'stderr' })
    },
  })

  const started = performance.now()
  let success = true
  let resultStr: string | null = null
  let error: RunResult['error'] = null

  try {
    const value = await pyodide.runPythonAsync(code)
    if (value !== undefined && value !== null) {
      try {
        resultStr = String(value)
      } catch {
        resultStr = '<unrepresentable result>'
      }
    }
  } catch (e) {
    success = false
    const err = e as Error
    error = {
      name: err.name || 'Error',
      message: err.message || String(e),
      trace: (err.stack || '').slice(0, 4000),
    }
  }

  const elapsedMs = Math.round(performance.now() - started)
  activeRunId = null
  setStatus('ready')

  post({
    type: 'run-result',
    id,
    success,
    stdout: stdoutBuf.join(''),
    stderr: stderrBuf.join(''),
    result: resultStr,
    error,
    elapsedMs,
  } satisfies RunResult)
}

function resetRuntime(id: string): void {
  if (pyodide) {
    try {
      pyodide.globals.clear()
    } catch {
      // ignore
    }
  }
  post({ type: 'reset-result', id, ok: true } satisfies ResetResult)
}

self.onmessage = (event: MessageEvent<WorkerInbound>) => {
  const msg = event.data
  switch (msg.type) {
    case 'run':
      void runCode(msg.id, msg.code)
      break
    case 'reset':
      resetRuntime(msg.id)
      break
  }
}

void bootPyodide().catch((e) => {
  setStatus('error')
  post({
    type: 'run-result',
    id: '_boot',
    success: false,
    stdout: '',
    stderr: '',
    result: null,
    error: { name: 'BootFailure', message: String(e), trace: (e as Error)?.stack ?? '' },
    elapsedMs: 0,
  })
})
