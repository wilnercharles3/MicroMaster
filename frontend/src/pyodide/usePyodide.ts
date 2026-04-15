// React hook for the shared Pyodide client. Exposes status, version,
// and a reactive `run` that re-renders the component while Python is
// executing. Output chunks are accumulated into a buffer the caller can
// clear between runs.

import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import { getPyodideClient } from './client'
import type { RunResult, WorkerStatus } from './types'

export interface PyodideRunState {
  running: boolean
  stdout: string
  stderr: string
  result: string | null
  error: RunResult['error']
  elapsedMs: number | null
}

const initialRunState: PyodideRunState = {
  running: false,
  stdout: '',
  stderr: '',
  result: null,
  error: null,
  elapsedMs: null,
}

export function usePyodide() {
  const client = useMemo(() => getPyodideClient(), [])
  const [status, setStatus] = useState<WorkerStatus>(client.status)
  const [loadingMsg, setLoadingMsg] = useState<string | null>(null)
  const [runState, setRunState] = useState<PyodideRunState>(initialRunState)
  const latestRunId = useRef(0)

  useEffect(() => {
    const offStatus = client.onStatus(setStatus)
    const offLoading = client.onLoading((_stage, message) => setLoadingMsg(message))
    return () => {
      offStatus()
      offLoading()
    }
  }, [client])

  const run = useCallback(
    async (code: string): Promise<RunResult> => {
      const runId = ++latestRunId.current
      setRunState({ ...initialRunState, running: true })

      const result = await client.run(code, (chunk) => {
        if (latestRunId.current !== runId) return
        setRunState((prev) => ({
          ...prev,
          [chunk.stream]: prev[chunk.stream] + chunk.text,
        }))
      })

      if (latestRunId.current === runId) {
        setRunState({
          running: false,
          stdout: result.stdout,
          stderr: result.stderr,
          result: result.result,
          error: result.error,
          elapsedMs: result.elapsedMs,
        })
      }
      return result
    },
    [client],
  )

  const reset = useCallback(async () => {
    await client.reset()
    setRunState(initialRunState)
  }, [client])

  const hardRestart = useCallback(() => {
    client.hardRestart()
    setRunState(initialRunState)
  }, [client])

  const clearOutput = useCallback(() => {
    setRunState(initialRunState)
  }, [])

  return {
    status,
    version: client.version,
    loadingMsg,
    run,
    reset,
    hardRestart,
    clearOutput,
    runState,
  }
}
