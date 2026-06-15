import { client } from './client'
import type {
  ChatResponse,
  Faq,
  Health,
  LoginResponse,
  RagStatus,
  RpaCommandResponse,
  RpaJobHistoryItem,
  RpaJobResult,
  Ticket,
  User,
} from './types'

// ---- Health & status ----
export const getHealth = () => client.get<Health>('/health').then((r) => r.data)
export const getRagStatus = () =>
  client.get<RagStatus>('/ai/status').then((r) => r.data)

// ---- Auth ----
export const login = (username: string, password: string) =>
  client
    .post<LoginResponse>('/users/login', { username, password })
    .then((r) => r.data)

// ---- AI ----
export const chat = (message: string) =>
  client.post<ChatResponse>('/ai/chat', { message }).then((r) => r.data)

export const aiRpa = (command: string) =>
  client.post<RpaCommandResponse>('/ai/rpa', { command }).then((r) => r.data)

// ---- Tickets ----
export interface TicketFilter {
  status?: string
  keyword?: string
  user?: string
}

export const listTickets = (params: TicketFilter = {}) =>
  client.get<Ticket[]>('/tickets', { params }).then((r) => r.data)

export const listAdminTickets = (params: Omit<TicketFilter, 'user'> = {}) =>
  client.get<Ticket[]>('/admin/tickets', { params }).then((r) => r.data)

export const getTicket = (id: number) =>
  client.get<Ticket>(`/tickets/${id}`).then((r) => r.data)

export const createTicket = (payload: {
  question: string
  user: string
  contact?: string
  category?: string
  priority?: string
}) => client.post<Ticket>('/tickets', payload).then((r) => r.data)

export const updateTicket = (id: number, payload: Record<string, unknown>) =>
  client.patch<Ticket>(`/tickets/${id}`, payload).then((r) => r.data)

export const resolveTicket = (
  id: number,
  payload: {
    resolution_note: string
    resolver: string
    add_to_kb: boolean
    kb_answer: string
    callback_status: string
    callback_note: string
  },
) => client.patch<Ticket>(`/admin/tickets/${id}/resolve`, payload).then((r) => r.data)

// ---- Users ----
export interface UserFilter {
  keyword?: string
  role?: string
  status?: string
}

export const listUsers = (params: UserFilter = {}) =>
  client.get<User[]>('/users', { params }).then((r) => r.data)

export const getUser = (id: number) =>
  client.get<User>(`/users/${id}`).then((r) => r.data)

export const createUser = (payload: Record<string, unknown>) =>
  client.post<User>('/users', payload).then((r) => r.data)

export const updateUser = (id: number, payload: Record<string, unknown>) =>
  client.put<User>(`/users/${id}`, payload).then((r) => r.data)

export const setUserStatus = (id: number, status: string) =>
  client.patch<User>(`/users/${id}/status`, { status }).then((r) => r.data)

export const deleteUser = (id: number) =>
  client.delete(`/users/${id}`).then((r) => r.data)

// ---- FAQ knowledge base ----
export const listFaqs = () =>
  client.get<Faq[]>('/admin/faqs').then((r) => r.data)

export const createFaq = (payload: {
  question: string
  answer: string
  tags: string[]
}) => client.post<Faq>('/admin/faqs', payload).then((r) => r.data)

export const updateFaq = (id: number, payload: Record<string, unknown>) =>
  client.patch<Faq>(`/admin/faqs/${id}`, payload).then((r) => r.data)

export const deleteFaq = (id: number) =>
  client.delete(`/admin/faqs/${id}`).then((r) => r.data)

// ---- RPA ----
export const listRpaJobs = () =>
  client.get<RpaJobHistoryItem[]>('/rpa-jobs').then((r) => r.data)

export const resetPassword = (payload: {
  username: string
  new_password: string
  requested_by?: string
}) => client.post<RpaJobResult>('/reset-password', payload).then((r) => r.data)

export const createAccountRpa = (payload: Record<string, unknown>) =>
  client.post<RpaJobResult>('/create-account', payload).then((r) => r.data)

export const freezeAccountRpa = (payload: {
  username: string
  requested_by?: string
  reason?: string
}) => client.post<RpaJobResult>('/freeze-account', payload).then((r) => r.data)

export const unfreezeAccountRpa = (payload: {
  username: string
  requested_by?: string
  reason?: string
}) => client.post<RpaJobResult>('/unfreeze-account', payload).then((r) => r.data)
