const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api/v1'
export const TOKEN_KEY = 'token'

export class AuthenticationError extends Error {
  constructor(message = '认证已过期，请重新登录') {
    super(message)
    this.name = 'AuthenticationError'
  }
}

interface RequestOptions {
  body?: unknown
  form?: URLSearchParams
  wrap401?: boolean
}

function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

async function request<T = unknown>(method: string, path: string, { body, form, wrap401 = true }: RequestOptions = {}): Promise<T> {
  const headers: Record<string, string> = {}
  const token = getToken()
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const options: RequestInit = { method, headers }

  if (form) {
    options.body = form
  } else if (body) {
    headers['Content-Type'] = 'application/json'
    options.body = JSON.stringify(body)
  }

  const res = await fetch(`${API_BASE}${path}`, options)

  if (res.status === 401) {
    if (wrap401) {
      localStorage.removeItem(TOKEN_KEY)
      throw new AuthenticationError()
    }
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || '用户名或密码错误')
  }

  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || `请求失败 (${res.status})`)
  }

  try {
    return await res.json()
  } catch {
    if (res.ok) return null as T
    throw new Error(`请求失败 (${res.status})`)
  }
}

export function apiGet<T = unknown>(path: string): Promise<T> {
  return request<T>('GET', path)
}

export function apiPost<T = unknown>(path: string, body?: unknown): Promise<T> {
  return request<T>('POST', path, { body })
}

export function apiPostForm<T = unknown>(path: string, formData: URLSearchParams): Promise<T> {
  return request<T>('POST', path, { form: formData, wrap401: false })
}

export function apiPatch<T = unknown>(path: string, body?: unknown): Promise<T> {
  return request<T>('PATCH', path, { body })
}

export function apiDelete<T = unknown>(path: string): Promise<T> {
  return request<T>('DELETE', path)
}
