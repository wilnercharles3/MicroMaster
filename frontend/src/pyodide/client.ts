// Main-thread client that talks to the Pyodide worker via postMessage.
// Exposes a promise-based `run` API and an event subscription for
// progressive stdout/stderr chunks so the UI can show output as it
// happens rather than all at once when the run finishes.

import type {
  ResetResult,
  RunResult,
  StdoutMessage,
  WorkerInbound,
  WorkerOutbound,
  WorkerStatus,
} from './types'

type Pending = {
  resolve: (r: RunResult) => void
  reject: (e: Error) => void
  onChunk?: (c: StdoutMessage) => void
}

export type StatusListener = (status: WorkerStatus) => void
export type LoadingListener = (stage: string, message: string) => void

export class PyodideClient {
  private worker: Worker
  private nextId = 1
  private pending = new Map<string, Pending>()
  private resetPending = new Map<string, (r: ResetResult) => void>()
  private statusListeners = new Set<StatusListener>()
  private loadingListeners = new Set<LoadingListener>()
  private _status: WorkerStatus = 'idle'
  private _version: string | null = null

  constructor() {
    // Vite picks up the special `new URL(..., import.meta.url)` syntax and
    // bundles the worker file as a separate chunk.
    this.worker = new Worker(new URL('./worker.ts', import.meta.url), {
      type: 'module',
    })
    this.worker.onmessage = (event: MessageEvent<WorkerOutbound>) => {
      this.handleMessage(event.data)
    }
    this.worker.onerror = (event) => {
      console.error('Pyodide worker error:', event.message)
    }
  }

  get status(): WorkerStatus {
    return this._status
  }

  get version(): string | null {
    return this._version
  }

  onStatus(fn: StatusListener): () => void {
    this.statusListeners.add(fn)
    fn(this._status)
    return () => this.statusListeners.delete(fn)
  }

  onLoading(fn: LoadingListener): () => void {
    this.loadingListeners.add(fn)
    return () => this.loadingListeners.delete(fn)
  }

  run(code: string, onChunk?: (c: StdoutMessage) => void): Promise<RunResult> {
    const id = `r${this.nextId++}`
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject, onChunk })
      this.post({ type: 'run', id, code })
    })
  }

  reset(): Promise<ResetResult> {
    const id = `x${this.nextId++}`
    return new Promise((resolve) => {
      this.resetPending.set(id, resolve)
      this.post({ type: 'reset', id })
    })
  }

  // Nuke the runtime and rebuild it. Used when a user's code hangs and
  // they click "Stop" - the only way to interrupt a running Python is
  // terminating the worker.
  hardRestart(): void {
    this.worker.terminate()
    for (const p of this.pending.values()) {
      p.reject(new Error('Worker restarted'))
    }
    this.pending.clear()
    this.resetPending.clear()
    this._status = 'idle'
    this._version = null
    this.statusListeners.forEach((l) => l('idle'))
    this.worker = new Worker(new URL('./worker.ts', import.meta.url), {
      type: 'module',
    })
    this.worker.onmessage = (event: MessageEvent<WorkerOutbound>) => {
      this.handleMessage(event.data)
    }
  }

  private post(msg: WorkerInbound): void {
    this.worker.postMessage(msg)
  }

  private handleMessage(msg: WorkerOutbound): void {
    switch (msg.type) {
      case 'status':
        this._status = msg.status
        this.statusListeners.forEach((l) => l(msg.status))
        break
      case 'loading-progress':
        this.loadingListeners.forEach((l) => l(msg.stage, msg.message))
        break
      case 'ready':
        this._version = msg.version
        break
      case 'stdout': {
        const p = this.pending.get(msg.id)
        if (p?.onChunk) p.onChunk(msg)
        break
      }
      case 'run-result': {
        const p = this.pending.get(msg.id)
        if (p) {
          this.pending.delete(msg.id)
          p.resolve(msg)
        }
        break
      }
      case 'reset-result': {
        const r = this.resetPending.get(msg.id)
        if (r) {
          this.resetPending.delete(msg.id)
          r(msg)
        }
        break
      }
    }
  }
}

// Lazy singleton. We create the worker only when the first sandbox asks
// for it, and reuse it across the whole app so variables persist
// between doses.
let singleton: PyodideClient | null = null

export function getPyodideClient(): PyodideClient {
  if (!singleton) {
    singleton = new PyodideClient()
  }
  return singleton
}
