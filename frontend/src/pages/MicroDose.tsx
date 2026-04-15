// The micro-dose viewer.
// Layout:
//   Left column  - hook, reading, teach-back draft.
//   Right column - code sandbox (copy-to-run for Phase 4), prompt
//                  reminder, save/complete actions.
// The completion button is only enabled once the user has either saved
// a draft or explicitly acknowledges completion - nothing is auto-awarded.

import { useCallback, useEffect, useRef, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { api } from '../api'
import { CodeSandbox } from '../components/CodeSandbox'
import { toast } from '../components/Toast'
import { useProgress } from '../state'
import type { DoseListEntry, MicroDose } from '../types'

export function MicroDosePage() {
  const { id } = useParams<{ id: string }>()
  const nav = useNavigate()
  const { refresh } = useProgress()

  const [dose, setDose] = useState<MicroDose | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const [code, setCode] = useState('')
  const [teachBack, setTeachBack] = useState('')
  const [saving, setSaving] = useState(false)
  const [completing, setCompleting] = useState(false)
  const [neighbors, setNeighbors] = useState<DoseListEntry[] | null>(null)
  const lastSaveRef = useRef<{ code: string; tb: string } | null>(null)

  useEffect(() => {
    if (!id) return
    const num = Number(id)
    api.dose(num).then(async (d) => {
      setDose(d)
      setCode(d.progress.last_code || d.starter_code || '')
      setTeachBack(d.progress.last_teach_back || '')
      lastSaveRef.current = { code: d.progress.last_code || d.starter_code || '', tb: d.progress.last_teach_back || '' }
      if (d.chapter_number) {
        try {
          const list = await api.chapterDoses(d.chapter_number)
          setNeighbors(list.doses)
        } catch { /* ignore */ }
      }
    }).catch((e) => setErr(String(e)))
  }, [id])

  const save = useCallback(async (silent = false) => {
    if (!dose) return
    const payload: { last_code?: string; last_teach_back?: string } = {}
    const snap = lastSaveRef.current
    if (!snap || code !== snap.code) payload.last_code = code
    if (!snap || teachBack !== snap.tb) payload.last_teach_back = teachBack
    if (Object.keys(payload).length === 0) return
    setSaving(true)
    try {
      const updated = await api.saveDose(dose.id, payload)
      setDose(updated)
      lastSaveRef.current = { code, tb: teachBack }
      if (!silent) toast('Draft saved')
    } catch (e) {
      if (!silent) toast(`Save failed: ${e}`)
    } finally {
      setSaving(false)
    }
  }, [dose, code, teachBack])

  // Autosave 4 seconds after the user stops typing.
  useEffect(() => {
    if (!dose) return
    const t = window.setTimeout(() => { void save(true) }, 4000)
    return () => window.clearTimeout(t)
  }, [dose, code, teachBack, save])

  const onComplete = useCallback(async () => {
    if (!dose) return
    setCompleting(true)
    try {
      await save(true)
      const updated = await api.completeDose(dose.id, 1.0)
      setDose(updated)
      toast(`Complete. +XP awarded.`)
      void refresh()
    } catch (e) {
      toast(`Complete failed: ${e}`)
    } finally {
      setCompleting(false)
    }
  }, [dose, save, refresh])

  const onNavigate = useCallback(async (targetId: number) => {
    await save(true)
    nav(`/doses/${targetId}`)
  }, [save, nav])

  if (err) return <div className="error">Error: {err}</div>
  if (!dose) return <div className="loading">Loading micro-dose...</div>

  const prev = neighbors ? neighbors[neighbors.findIndex((d) => d.id === dose.id) - 1] : undefined
  const next = neighbors ? neighbors[neighbors.findIndex((d) => d.id === dose.id) + 1] : undefined

  return (
    <>
      <div className="meta-row">
        <Link to="/">Chapters</Link> /{' '}
        {dose.chapter_number != null ? (
          <Link to={`/chapters/${dose.chapter_number}`}>Ch {dose.chapter_number} {dose.chapter_title}</Link>
        ) : (
          <span>chapter</span>
        )}{' '}/{' '}
        Micro-dose {dose.order_index + 1}
      </div>
      <h1>{dose.title}</h1>
      <div className="meta-row">
        Source: <span>{dose.source_ref}</span> &middot; {dose.char_count} chars &middot;{' '}
        <span className={`pill status-${dose.progress.status}`}>{dose.progress.status.replace('_', ' ')}</span>
      </div>

      {dose.hook && <div className="hook">{dose.hook}</div>}

      <div className="dose-layout">
        <div className="dose-main">
          <div className="card">
            <h2>Reading</h2>
            <div className="reading">{dose.reading}</div>
          </div>

          <div className="card teach-back" style={{ marginTop: 18 }}>
            <h3>Teach-back</h3>
            <p className="meta-row" style={{ marginTop: 0 }}>{dose.teach_back_prompt}</p>
            <textarea
              value={teachBack}
              onChange={(e) => setTeachBack(e.target.value)}
              placeholder="Explain the idea in your own words..."
            />
            <div className="sandbox-hint">
              Phase 10 wires up Claude API to evaluate this for accuracy and completeness.
            </div>
          </div>

          <div className="dose-nav">
            <button onClick={() => prev && onNavigate(prev.id)} disabled={!prev}>
              {prev ? `< ${prev.title}` : 'First dose'}
            </button>
            <button
              className="success"
              onClick={onComplete}
              disabled={completing || dose.progress.status === 'completed'}
            >
              {dose.progress.status === 'completed' ? 'Completed' : completing ? 'Saving...' : 'Mark complete'}
            </button>
            <button onClick={() => next && onNavigate(next.id)} disabled={!next}>
              {next ? `${next.title} >` : 'Last dose'}
            </button>
          </div>
        </div>

        <aside className="dose-side">
          <CodeSandbox value={code} onChange={setCode} onSave={() => void save()} saving={saving} />
        </aside>
      </div>
    </>
  )
}

