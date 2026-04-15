// Phase 4 sandbox: a plain textarea with a copy-to-clipboard button and
// a "mark run" flag. Phase 6 replaces this with a Pyodide-backed runner
// while keeping the same props API.

import { useState } from 'react'

interface Props {
  value: string
  onChange: (v: string) => void
  onSave?: () => void
  saving?: boolean
  disabled?: boolean
}

export function CodeSandbox({ value, onChange, onSave, saving, disabled }: Props) {
  const [copied, setCopied] = useState(false)

  async function copy() {
    try {
      await navigator.clipboard.writeText(value || '')
      setCopied(true)
      window.setTimeout(() => setCopied(false), 1500)
    } catch {
      setCopied(false)
    }
  }

  return (
    <div className="card sandbox">
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
        <h3 style={{ margin: 0 }}>Code sandbox</h3>
        <span className="pill">copy-to-run (Phase 4)</span>
      </div>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        spellCheck={false}
        placeholder="# Your Python code here"
        disabled={disabled}
      />
      <div className="sandbox-actions">
        <button onClick={copy}>{copied ? 'Copied' : 'Copy code'}</button>
        {onSave && (
          <button onClick={onSave} disabled={saving}>
            {saving ? 'Saving...' : 'Save draft'}
          </button>
        )}
      </div>
      <div className="sandbox-hint">
        Phase 4 runs code by copy-paste into your own Python shell. Phase 6 wires
        up an in-browser Python runtime (Pyodide) so you can execute here.
      </div>
    </div>
  )
}
