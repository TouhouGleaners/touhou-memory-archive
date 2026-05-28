const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'

function getToken() {
  return localStorage.getItem('token')
}

function clearToken() {
  localStorage.removeItem('token')
}

async function request(method, path, { body, form } = {}) {
  const headers = {}
  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const options = { method, headers }

  if (form) {
    // OAuth2 表单登录，不设 Content-Type（浏览器自动加 boundary）
    options.body = form
  } else if (body) {
    headers['Content-Type'] = 'application/json'
    options.body = JSON.stringify(body)
  }

  const res = await fetch(`${API_BASE}${path}`, options)

  if (res.status === 401) {
    clearToken()
    window.location.hash = '#/admin/login'
    throw new Error('认证已过期，请重新登录')
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
  return request('POST', path, { form: formData })
}

export function apiPatch(path, body) {
  return request('PATCH', path, { body })
}
