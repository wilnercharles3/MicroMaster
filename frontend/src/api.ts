// Thin typed wrapper around fetch. The Vite dev proxy forwards /api to
// the Flask backend so the same calls work in production behind a
// reverse proxy.
import type {
  ChapterDetail,
  ChapterSummary,
  DoseListResponse,
  ExerciseDetail,
  MicroDose,
  PracticeList,
  ProgressResponse,
  XpEvent,
} from './types'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    headers: { 'content-type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const body = await res.text().catch(() => '')
    throw new Error(`${res.status} ${res.statusText} on ${path}: ${body}`)
  }
  return (await res.json()) as T
}

export const api = {
  health: () => request<{ status: string; db: string }>('/api/health'),

  chapters: () => request<{ chapters: ChapterSummary[] }>('/api/chapters'),

  chapter: (number: number) => request<ChapterDetail>(`/api/chapters/${number}`),

  chapterDoses: (number: number) =>
    request<DoseListResponse>(`/api/chapters/${number}/micro-doses`),

  dose: (id: number) => request<MicroDose>(`/api/micro-doses/${id}`),

  saveDose: (id: number, body: { last_code?: string; last_teach_back?: string }) =>
    request<MicroDose>(`/api/micro-doses/${id}/save`, {
      method: 'POST',
      body: JSON.stringify(body),
    }),

  completeDose: (id: number, score = 1.0) =>
    request<MicroDose>(`/api/micro-doses/${id}/complete`, {
      method: 'POST',
      body: JSON.stringify({ score }),
    }),

  practice: (chapterNumber: number) =>
    request<PracticeList>(`/api/chapters/${chapterNumber}/practice`),

  exercise: (id: number) => request<ExerciseDetail>(`/api/practice/${id}`),

  submitExercise: (id: number, body: { passed: boolean; code?: string }) =>
    request<{ id: number; passed: boolean; awarded_xp: boolean; status: string }>(
      `/api/practice/${id}/submit`,
      { method: 'POST', body: JSON.stringify(body) },
    ),

  progress: () => request<ProgressResponse>('/api/progress'),

  xpEvents: (limit = 20) =>
    request<{ events: XpEvent[] }>(`/api/xp/events?limit=${limit}`),
}
