// TypeScript types aligned with backend/models/schemas.py

export type Role = 'admin' | 'operator' | 'viewer'
export type AccountStatus = 'active' | 'frozen'
export type TicketStatus = 'open' | 'in_progress' | 'resolved' | 'closed'
export type Priority = 'low' | 'normal' | 'high' | 'urgent'
export type CallbackStatus = 'pending' | 'contacted' | 'closed'

export interface User {
  id: number
  username: string
  role: Role
  full_name: string
  department: string
  phone: string
  email: string
  status: AccountStatus
  created_at: string
  updated_at: string
}

export interface LoginResponse {
  token: string
  user: User
}

export interface RagSource {
  id: number
  question: string
  answer: string
  tags: string[]
  score: number
}

export interface RagStatus {
  mode: string
  faq_count: number
  confidence_threshold: number
  direct_answer_threshold: number
  llm_provider: string
  vector_store: string
  scorer: string
}

export interface ChatResponse {
  intent: string
  type: string
  content: string
  confidence?: number | null
  ticket_id?: number | null
  success?: boolean | null
  action?: string | null
  steps?: string[] | null
  sources?: Record<string, unknown>[] | null
}

export interface Ticket {
  id: number
  question: string
  user: string
  contact: string
  category: string
  priority: Priority
  status: TicketStatus
  answer: string | null
  resolver: string | null
  callback_status: CallbackStatus
  callback_note: string | null
  created_at: string
  updated_at: string
  resolved_at: string | null
}

export interface Faq {
  id: number
  question: string
  answer: string
  tags: string[]
}

export interface RpaJobResult {
  job_id: number
  action: string
  status: string
  result: string
  steps: string[]
}

export interface RpaCommandResponse {
  success: boolean
  action: string
  message: string
  steps?: string[] | null
  status?: string | null
}

export interface RpaJobHistoryItem {
  id: number
  action: string
  payload: string
  status: string
  result: string
  created_at: string
}

export interface Health {
  status: string
  service: string
}
