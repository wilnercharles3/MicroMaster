// Phase 4 home page: plain chapter grid with per-chapter progress bars.
// Phase 5 replaces this with the full roadmap visualization.

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'

import { api } from '../api'
import type { ChapterSummary } from '../types'

export function HomePage() {
  const [chapters, setChapters] = useState<ChapterSummary[] | null>(null)
  const [err, setErr] = useState<string | null>(null)

  useEffect(() => {
    api.chapters().then((r) => setChapters(r.chapters)).catch((e) => setErr(String(e)))
  }, [])

  if (err) return <div className="error">Error loading chapters: {err}</div>
  if (!chapters) return <div className="loading">Loading chapters...</div>

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 12, marginBottom: 14 }}>
        <h1>Chapters</h1>
        <span className="meta-row">{chapters.length} total. Phase 4 preview - a visual roadmap replaces this grid in Phase 5.</span>
      </div>
      <div className="grid-chapters">
        {chapters.map((c) => (
          <ChapterCard key={c.number} c={c} />
        ))}
      </div>
      <div className="attribution">
        Source: <em>Automate the Boring Stuff with Python, 3rd Edition</em> and its Workbook by
        Al Sweigart. Displayed locally for personal study use.
      </div>
    </>
  )
}

function ChapterCard({ c }: { c: ChapterSummary }) {
  const learnTotal = c.totals.learn_doses || 1
  const practiceTotal = c.totals.practice_exercises || 1
  const learnPct = (c.completed.learn_doses / learnTotal) * 100
  const practicePct = (c.completed.practice_exercises / practiceTotal) * 100

  return (
    <Link to={`/chapters/${c.number}`} className="chapter-card">
      <div className="ch-num">Chapter {c.number}</div>
      <div className="ch-title">{c.title}</div>
      <div className="ch-stats">
        <span className="pill learn">Learn {c.completed.learn_doses}/{c.totals.learn_doses}</span>
        <span className="pill practice">Practice {c.completed.practice_exercises}/{c.totals.practice_exercises}</span>
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 6 }}>
        <div className="bar learn"><span style={{ width: `${learnPct}%` }} /></div>
        <div className="bar practice"><span style={{ width: `${practicePct}%` }} /></div>
      </div>
    </Link>
  )
}
