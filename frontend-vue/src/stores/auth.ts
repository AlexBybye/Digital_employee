import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { AUTH_KEY } from '@/api/client'
import { login as apiLogin } from '@/api'
import type { Role, User } from '@/api/types'

interface StoredAuth {
  token: string
  user: User
}

function load(): StoredAuth | null {
  try {
    const raw = localStorage.getItem(AUTH_KEY)
    return raw ? (JSON.parse(raw) as StoredAuth) : null
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', () => {
  const initial = load()
  const token = ref<string | null>(initial?.token ?? null)
  const user = ref<User | null>(initial?.user ?? null)

  const isLoggedIn = computed(() => !!token.value)
  const role = computed<Role | null>(() => user.value?.role ?? null)
  const username = computed(() => user.value?.username ?? '')

  async function login(name: string, password: string) {
    const data = await apiLogin(name, password)
    token.value = data.token
    user.value = data.user
    localStorage.setItem(AUTH_KEY, JSON.stringify(data))
    return data
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem(AUTH_KEY)
  }

  return { token, user, isLoggedIn, role, username, login, logout }
})
