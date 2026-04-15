// Chapter detail: two columns - Learn-track micro-doses on the left,
// Practice-track workbook exercises on the right. Clicking a dose
// routes to the dose viewer.

import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { api } from '../api'
import type { ChapterDetail, DoseListResponse, PracticeList } from '../types'

export function ChapterPage() {
  const { number } = useParams<{ number: string }>()
  const num = Number(number)
  const [detail, setDetail] = useState<ChapterDetail | null>(null)
  const [doses, setDoses] = useState<DoseListResponse | null>(null)
  const [practice, setPractice] = useState<PracticeList | null>(null)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    if (!num) return
    setDetail(null); setDoses(null); setPractice(null); setErr(null)
    Promise.all([
      api.chapter(num),
      api.chapterDoses(num),
      api.practice(num),
    ]).then(([d, ds, p]) => { setDetail(d); setDoses(ds); setPractice(p) })
      .catch((e) => setErr(String(e)))
  }, [num])

  if (err) return <div className="error">Error: {err}</div>
  if (!detail || !doses || !practice) return <div className="loading">Loading chapter...</div>

  return (
    <>
      <div className="meta-row"><Link to="/">All chapters</Link> / Chapter {detail.number}</div>
      <h1>Ch {detail.number}: {detail.title}</h1>
      <div className="meta-row">
        Book p{detail.book_pages[0]}-{detail.book_pages[1]} &middot; {detail.totals.sections} sections &middot; {detail.totals.learn_doses} micro-doses &middot; {detail.totals.practice_exercises} practice exercises
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.2fr) minmax(0, 1fr)', gap: 22, marginTop: 22 }}>
        <section className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
            <h2 style={{ margin: 0 }}>Learn track</h2>
            <span className="pill learn">{doses.count} doses</span>
          </div>
          <ul className="section-list">
            {doses.doses.map((d) => (
              <li key={d.id}>
                <Link to={`/doses/${d.id}`} style={{ display: 'block' }}>
                  <div style={{ fontWeight: 600 }}>{d.title}</div>
                  <div className="meta-row">{d.hook || '(no hook)'}</div>
                  <div className="meta-row">{d.char_count} chars</div>
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <section className="card">
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
            <h2 style={{ margin: 0 }}>Practice track</h2>
            <span className="pill practice">{practice.exercises.length} exercises</span>
          </div>
          <ul className="section-list">
            {practice.exercises.map((ex) => (
              <li key={ex.id}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 600 }}>{ex.title}</div>
                    <div className="meta-row">{ex.kind === 'question' ? 'practice question' : 'practice project'}</div>
                  </div>
                  {ex.completed && <span className="pill status-completed">done</span>}
                </div>
              </li>
            ))}
          </ul>
          <div className="meta-row" style={{ marginTop: 14 }}>
            Practice-track viewer ships in Phase 7b alongside the vocab/syntax node.
          </div>
        </section>
      </div>
    </>
  )
}
