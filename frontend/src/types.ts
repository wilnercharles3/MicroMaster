// Shared types matching the Flask API's JSON shapes. Kept deliberately
// small - these are structural contracts, not class hierarchies.

export type NodeKind =
  | 'learn_dose'
  | 'practice_exercise'
  | 'miniproject'
  | 'boss_battle'
  | 'vocab'
  | 'syntax'

export type ProgressStatus = 'locked' | 'available' | 'in_progress' | 'completed'

export interface ChapterSummary {
  number: number
  title: string
  source_ref: string
  book_pages: [number, number]
  workbook_number: number | null
  workbook_title: string | null
  workbook_pages: [number, number] | null
  totals: { sections: number; learn_doses: number; practice_exercises: number }
  completed: { learn_doses: number; practice_exercises: number }
}

export interface SectionRow {
  id: number
  order_index: number
  title: string
  depth: number
  pages: [number, number]
  source_ref: string
  char_count: number
}

export interface ChapterDetail extends ChapterSummary {
  sections: SectionRow[]
}

export interface DoseListEntry {
  id: number
  order_index: number
  title: string
  hook: string
  char_count: number
}

export interface DoseListResponse {
  chapter_number: number
  chapter_title: string
  count: number
  doses: DoseListEntry[]
}

export interface DoseProgress {
  status: ProgressStatus
  score: number
  completed_at: string | null
  last_code: string
  last_teach_back: string
}

export interface MicroDose {
  id: number
  chapter_id: number
  chapter_number: number | null
  chapter_title: string | null
  section_id: number
  order_index: number
  title: string
  hook: string
  reading: string
  starter_code: string
  teach_back_prompt: string
  quiz_json: string
  char_count: number
  source_ref: string
  progress: DoseProgress
}

export interface PracticeExercise {
  id: number
  kind: 'question' | 'project'
  title: string
  order_index: number
  source_ref: string
  completed: boolean
}

export interface PracticeSection {
  id: number
  kind: 'objectives' | 'questions' | 'projects'
  title: string
  text_preview: string
}

export interface PracticeList {
  chapter_number: number
  chapter_title: string
  sections: PracticeSection[]
  exercises: PracticeExercise[]
}

export interface ExerciseDetail {
  id: number
  chapter_id: number
  kind: 'question' | 'project'
  title: string
  text: string
  source_ref: string
  progress: {
    status: ProgressStatus
    score: number
    last_code: string
    completed_at: string | null
  }
}

export interface LevelInfo {
  name: string
  min_xp: number
  next_name: string | null
  next_min_xp: number | null
  xp_into_level: number
  xp_to_next: number | null
}

export interface ChapterRollup {
  number: number
  title: string
  learn: { total: number; completed: number; ratio: number }
  practice: { total: number; completed: number; ratio: number }
  miniproject: { completed: boolean; ratio: number }
  chapter_score: number
}

export interface ProgressResponse {
  user_id: string
  total_xp: number
  level: LevelInfo
  streak: { days: number; multiplier: number }
  overall_score: number
  chapters: ChapterRollup[]
  as_of: string
}

export interface XpEvent {
  id: number
  event_type: string
  amount: number
  multiplier: number
  reference_kind: string
  reference_id: number
  occurred_at: string
}
