import { reactive, computed } from 'vue'
import { apiGet, apiPostForm, AuthenticationError, TOKEN_KEY } from '../api/client'

// token 存 localStorage：简单直接，适合管理员后台场景。
// 若未来需要更高安全性，可改为 HttpOnly Cookie + 后端配合。

interface AuthState {
  token: string | null
  user: { id: number; username: string; role: string } | null
}

let isFetchingUser = false

const state = reactive<AuthState>({
  token: localStorage.getItem(TOKEN_KEY) || null,
  user: null,
})

function clearAuth() {
  state.token = null
  state.user = null
  localStorage.removeItem(TOKEN_KEY)
}

export function useAuth() {
  const isLoggedIn = computed(() => !!state.token)

  async function login(username: string, password: string) {
    const form = new URLSearchParams()
    form.append('username', username)
    form.append('password', password)

    const data = await apiPostForm<{ access_token: string }>('/auth/login', form)
    state.token = data.access_token
    localStorage.setItem(TOKEN_KEY, data.access_token)
    await fetchUser()
  }

  async function fetchUser() {
    if (!state.token || isFetchingUser) return
    isFetchingUser = true
    try {
      state.user = await apiGet<AuthState['user']>('/auth/me')
    } catch (e) {
      if (e instanceof AuthenticationError) {
        clearAuth()
      } else {
        console.error('获取用户信息失败:', e)
      }
    } finally {
      isFetchingUser = false
    }
  }

  function logout() {
    clearAuth()
  }

  return {
    state,
    isLoggedIn,
    login,
    logout,
    fetchUser,
  }
}
