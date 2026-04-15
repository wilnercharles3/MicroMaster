// Progress context: one lightweight global cache for XP/level/streak so
// the header can refresh after a dose is completed.
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'

import { api } from './api'
import type { ProgressResponse } from './types'

interface ProgressState {
  progress: ProgressResponse | null
  loading: boolean
  refresh: () => Promise<void>
}

const Ctx = createContext<ProgressState | undefined>(undefined)

export function ProgressProvider({ children }: { children: ReactNode }) {
  const [progress, setProgress] = useState<ProgressResponse | null>(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    try {
      const data = await api.progress()
      setProgress(data)
    } catch (err) {
      console.error('progress fetch failed', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const value = useMemo(() => ({ progress, loading, refresh }), [progress, loading, refresh])
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useProgress(): ProgressState {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useProgress must be used inside ProgressProvider')
  return ctx
}
