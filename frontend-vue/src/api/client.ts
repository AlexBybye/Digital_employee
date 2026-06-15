import axios, { AxiosError } from 'axios'
import { ElMessage } from 'element-plus'

const AUTH_KEY = 'ops_digital_employee_auth'

interface StoredAuth {
  token: string
  user: unknown
}

function readToken(): string | null {
  try {
    const raw = localStorage.getItem(AUTH_KEY)
    if (!raw) return null
    const parsed = JSON.parse(raw) as StoredAuth
    return parsed?.token ?? null
  } catch {
    return null
  }
}

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8001',
  headers: { 'Content-Type': 'application/json' },
})

// Attach Bearer token to every request when logged in.
client.interceptors.request.use((config) => {
  const token = readToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Normalize errors; auto-logout on 401 (token expired/invalid).
client.interceptors.response.use(
  (response) => response,
  (error: AxiosError<{ detail?: string }>) => {
    const status = error.response?.status
    const detail = error.response?.data?.detail
    const message =
      (typeof detail === 'string' && detail) || error.message || '请求失败'

    if (status === 401) {
      // Clear stale auth; let the router guard redirect to login.
      localStorage.removeItem(AUTH_KEY)
      if (!location.hash.includes('/login')) {
        ElMessage.warning('登录已失效，请重新登录')
        location.hash = '#/login'
      }
    }
    return Promise.reject(new Error(message))
  },
)

export { client, AUTH_KEY }
