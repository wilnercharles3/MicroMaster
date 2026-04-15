// Tiny transient notification shown in the bottom center. Used when a
// micro-dose is completed to surface the XP award visibly.

import { useEffect, useState } from 'react'

export type ToastMessage = { id: number; text: string }

let counter = 0
const listeners = new Set<(m: ToastMessage) => void>()

export function toast(text: string) {
  const msg = { id: ++counter, text }
  for (const fn of listeners) fn(msg)
}

export function ToastHost() {
  const [visible, setVisible] = useState<ToastMessage | null>(null)
  useEffect(() => {
    const onMessage = (m: ToastMessage) => {
      setVisible(m)
      window.setTimeout(() => setVisible((cur) => (cur && cur.id === m.id ? null : cur)), 2500)
    }
    listeners.add(onMessage)
    return () => { listeners.delete(onMessage) }
  }, [])
  if (!visible) return null
  return <div className="toast">{visible.text}</div>
}
