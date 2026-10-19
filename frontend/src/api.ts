export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export async function api<T>(url: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  if (init.body && !(init.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  const response = await fetch(url, {
    ...init,
    headers,
    credentials: 'same-origin',
  })
  const contentType = response.headers.get('content-type') || ''
  const payload = contentType.includes('application/json')
    ? await response.json()
    : await response.text()
  if (!response.ok) {
    const message = typeof payload === 'object' && payload && 'msg' in payload
      ? String(payload.msg)
      : `请求失败 (${response.status})`
    throw new ApiError(message, response.status)
  }
  return payload as T
}

export interface Course {
  id: number
  name: string
  teacher?: string
  teacher_id?: number | null
  credit: number
  type?: string
  intro?: string
  reason?: string
}

export interface UserSession {
  authenticated: boolean
  role?: 'student' | 'teacher' | 'admin'
  user_id?: number
  name?: string
}
