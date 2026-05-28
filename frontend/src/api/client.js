const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

export class AuthenticationError extends Error {
  constructor(message = '认证已过期，请重新登录') {
    super(message)
    this.name = 'AuthenticationError'
  }
}

function getToken() {
  return localStorage.getItem('token')
}

async function request(method, path, { body, form, wrap401 = true } = {}) {
  const headers = {}
  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const options = { method, headers }

  if (form) {
    options.body = form
  } else if (body) {
    headers['Content-Type'] = 'application/json'
    options.body = JSON.stringify(body)
  }

  const res = await fetch(`${API_BASE}${path}`, options)

  if (res.status === 401) {
    if (wrap401) throw new AuthenticationError()
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || '用户名或密码错误')
  }

  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || `请求失败 (${res.status})`)
  }

  return res.json()
}

export function apiGet(path) {
  return request('GET', path)
}

export function apiPost(path, body) {
  return request('POST', path, { body })
}

export function apiPostForm(path, formData) {
  return request('POST', path, { form: formData, wrap401: false })
}

export function apiPatch(path, body) {
  return request('PATCH', path, { body })
}
