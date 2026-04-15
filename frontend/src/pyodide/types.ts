// Message contract between the main thread and the Pyodide web worker.
// Every request carries an id so the main-thread client can match
// responses to their awaiting promises.

export type WorkerStatus = 'idle' | 'loading' | 'ready' | 'running' | 'error'

export interface LoadingProgress {
  type: 'loading-progress'
  stage: 'boot' | 'pyodide' | 'ready'
  message: string
}

export interface StatusMessage {
  type: 'status'
  status: WorkerStatus
}

export interface ReadyMessage {
  type: 'ready'
  version: string
}

export interface RunRequest {
  type: 'run'
  id: string
  code: string
}

export interface ResetRequest {
  type: 'reset'
  id: string
}

export interface StdoutMessage {
  type: 'stdout'
  id: string
  text: string
  stream: 'stdout' | 'stderr'
}

export interface RunResult {
  type: 'run-result'
  id: string
  success: boolean
  stdout: string
  stderr: string
  result: string | null
  error: {
    name: string
    message: string
    trace: string
  } | null
  elapsedMs: number
}

export interface ResetResult {
  type: 'reset-result'
  id: string
  ok: boolean
}

export type WorkerOutbound =
  | StatusMessage
  | LoadingProgress
  | ReadyMessage
  | StdoutMessage
  | RunResult
  | ResetResult

export type WorkerInbound = RunRequest | ResetRequest
