// XP, level, and streak strip shown in the app header.
import { useProgress } from '../state'

export function ProgressHeader() {
  const { progress, loading } = useProgress()
  if (loading || !progress) {
    return <div className="progress-strip" aria-hidden><span className="pill">loading</span></div>
  }
  const { total_xp, level, streak } = progress
  const xpIn = level.xp_into_level
  const xpSpan = level.next_min_xp != null ? level.next_min_xp - level.min_xp : 1
  const pct = level.xp_to_next != null ? Math.min(100, (xpIn / xpSpan) * 100) : 100

  return (
    <div className="progress-strip">
      <span className="pill" title="Current level">{level.name}</span>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, minWidth: 200 }}>
        <span style={{ fontFamily: 'var(--mono)', fontSize: 13 }}>{total_xp} XP</span>
        <div className="bar xp" style={{ flex: 1, minWidth: 90 }} title={level.xp_to_next != null ? `${level.xp_to_next} XP to ${level.next_name}` : 'Max level'}>
          <span style={{ width: `${pct}%` }} />
        </div>
      </div>
      <span className="pill" title={`x${streak.multiplier} XP multiplier`}>
        streak {streak.days}d
      </span>
    </div>
  )
}
