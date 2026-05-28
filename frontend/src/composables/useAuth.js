import { reactive, computed } from 'vue'
import { apiGet, apiPostForm, AuthenticationError } from '../api/client.js'

const state = reactive({
  token: localStorage.getItem('token') || null,
  user: null,
})

function clearAuth() {
  state.token = null
  state.user = null
  localStorage.removeItem('token')
}

export function useAuth() {
  const isLoggedIn = computed(() => !!state.token)

  async function login(username, password) {
    const form = new URLSearchParams()
    form.append('username', username)
    form.append('password', password)

    const data = await apiPostForm('/auth/login', form)
    state.token = data.access_token
    localStorage.setItem('token', data.access_token)
    await fetchUser()
  }

  async function fetchUser() {
    if (!state.token) return
    try {
      state.user = await apiGet('/auth/me')
    } catch {
      clearAuth()
    }
  }

  function logout() {
    clearAuth()
  }

  // 如果有 token 但没有 user 信息，自动获取
  if (state.token && !state.user) {
    fetchUser()
  }

  return {
    state,
    isLoggedIn,
    login,
    logout,
    fetchUser,
  }
}
