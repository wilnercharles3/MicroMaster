// Phase 6 sandbox: real Pyodide-backed Python runtime.
//
// Python runs in a Web Worker (see src/pyodide/*). The first run pays a
// one-time load cost; subsequent runs are fast and share globals, so
// variables defined here persist across doses for a scratch-REPL feel.

import { useEffect, useRef, useState } from 'react'

import { usePyodide } from '../pyodide/usePyodide'

interface Props {
  value: string
  onChange: (v: string) => void
  onSave?: () => void
  saving?: boolean
  disabled?: boolean
  // Optional expected output for lightweight "did it pass" check.
  expectedStdout?: string
  // Callback fired when the run finishes, receives the pass/fail.
  onRunResult?: (info: { passed: boolean | null; stdout: string; errored: boolean }) => void
}

export function CodeSandbox({
  value,
  onChange,
  onSave,
  saving,
  disabled,
  expectedStdout,
  onRunResult,
}: Props) {
  const { status, loadingMsg, run, reset, hardRestart, clearOutput, runState } = usePyodide()
  const [copied, setCopied] = useState(false)
  const [lastPassed, setLastPassed] = useState<boolean | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)

  async function copy() {
    try {
      await navigator.clipboard.writeText(value || '')
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1500)
    } catch {
      setCopied(false)
    }
  }

  async function doRun() {
    setLastPassed(null)
    const res = await run(value || '')
    let passed: boolean | null = null
    if (expectedStdout != null) {
      const wanted = expectedStdout.replace(/\s+$/g, '')
      const got = (res.stdout || '').replace(/\s+$/g, '')
      passed = !res.error && got === wanted
      setLastPassed(passed)
    }
    onRunResult?.({ passed, stdout: res.stdout, errored: !!res.error })
  }

  // Ctrl+Enter / Cmd+Enter to run from the textarea.
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault()
        void doRun()
      }
    }
    el.addEventListener('keydown', onKey)
    return () => el.removeEventListener('keydown', onKey)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value, expectedStdout])

  const booting = status === 'loading' || status === 'idle'
  const running = runState.running || status === 'running'

  return (
    <div className="card sandbox">
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8, flexWrap: 'wrap' }}>
        <h3 style={{ margin: 0 }}>Python sandbox</h3>
        <SandboxStatusPill status={status} loadingMsg={loadingMsg} />
        {expectedStdout != null && lastPassed === true && <span className="pill status-completed">passed</span>}
        {expectedStdout != null && lastPassed === false && <span className="pill" style={{ color: 'var(--danger)', borderColor: 'rgba(232,90,90,0.4)' }}>output mismatch</span>}
      </div>
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        spellCheck={false}
        placeholder="# Python. Ctrl+Enter to run."
        disabled={disabled || running}
      />
      <div className="sandbox-actions">
        <button className="primary" onClick={doRun} disabled={booting || running}>
          {running ? 'Running...' : booting ? 'Loading Python...' : 'Run  (Ctrl+Enter)'}
        </button>
        <button onClick={copy}>{copied ? 'Copied' : 'Copy'}</button>
        {onSave && (
          <button onClick={onSave} disabled={saving}>
            {saving ? 'Saving...' : 'Save draft'}
          </button>
        )}
        <button
          onClick={() => void reset()}
          disabled={running}
          title="Clear Python globals. Variables go away but the runtime stays loaded."
        >
          Reset vars
        </button>
        {running && (
          <button
            onClick={hardRestart}
            title="Force-terminate. Use if code hangs in an infinite loop."
            style={{ marginLeft: 'auto', borderColor: 'var(--danger)', color: 'var(--danger)' }}
          >
            Stop
          </button>
        )}
        <button onClick={clearOutput} title="Clear the output panel below">
          Clear output
        </button>
      </div>

      <OutputPanel
        stdout={runState.stdout}
        stderr={runState.stderr}
        result={runState.result}
        error={runState.error}
        elapsedMs={runState.elapsedMs}
      />

      {expectedStdout != null && (
        <div className="sandbox-hint">
          Expected output:
          <pre style={{ margin: 6, padding: 8, background: '#0c0f16', border: '1px solid var(--border)', borderRadius: 6, whiteSpace: 'pre-wrap', fontSize: 12 }}>
            {expectedStdout}
          </pre>
        </div>
      )}

      <div className="sandbox-hint">
        Runs in your browser via Pyodide. Globals persist across doses so you can
        build on earlier snippets. "Reset vars" clears them.
      </div>
    </div>
  )
}

function SandboxStatusPill({ status, loadingMsg }: { status: string; loadingMsg: string | null }) {
  if (status === 'idle') return <span className="pill">starting</span>
  if (status === 'loading') return <span className="pill">{loadingMsg || 'loading'}</span>
  if (status === 'running') return <span className="pill status-in_progress">running</span>
  if (status === 'error') return <span className="pill" style={{ color: 'var(--danger)' }}>error</span>
  return <span className="pill status-completed">ready</span>
}

function OutputPanel({
  stdout,
  stderr,
  result,
  error,
  elapsedMs,
}: {
  stdout: string
  stderr: string
  result: string | null
  error: { name: string; message: string; trace: string } | null
  elapsedMs: number | null
}) {
  const empty = !stdout && !stderr && !result && !error
  if (empty) return null
  return (
    <div
      className="card"
      style={{
        marginTop: 10,
        background: '#0c0f16',
        border: '1px solid var(--border)',
        padding: 12,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
        <strong style={{ fontSize: 13 }}>Output</strong>
        {elapsedMs != null && <span className="meta-row">{elapsedMs} ms</span>}
      </div>
      {stdout && (
        <pre style={{ margin: 0, padding: 0, whiteSpace: 'pre-wrap', fontFamily: 'var(--mono)', fontSize: 13 }}>
          {stdout}
        </pre>
      )}
      {stderr && (
        <pre
          style={{
            margin: '6px 0 0',
            padding: 0,
            whiteSpace: 'pre-wrap',
            fontFamily: 'var(--mono)',
            fontSize: 13,
            color: 'var(--vocab)',
          }}
        >
          {stderr}
        </pre>
      )}
      {result && !stdout && !error && (
        <pre style={{ margin: 0, padding: 0, whiteSpace: 'pre-wrap', fontFamily: 'var(--mono)', fontSize: 13, color: 'var(--text-dim)' }}>
          {result}
        </pre>
      )}
      {error && (
        <pre
          style={{
            margin: '6px 0 0',
            padding: 0,
            whiteSpace: 'pre-wrap',
            fontFamily: 'var(--mono)',
            fontSize: 13,
            color: 'var(--danger)',
          }}
        >
          {error.name}: {error.message}
          {error.trace ? `\n\n${error.trace}` : ''}
        </pre>
      )}
    </div>
  )
}
