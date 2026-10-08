/**
 * Thin fetch layer. Same origin as the API (the Python service serves both), relative URLs only —
 * there is no second host, no CORS, and no outbound network dependency in this app.
 */
import type { ApiError } from './types'

export class SutraApiError extends Error {
  status: number
  code: string
  constructor(status: number, body: Partial<ApiError>) {
    super(body.detail || body.error || `HTTP ${status}`)
    this.status = status
    this.code = body.error || 'http_error'
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
  })
  const text = await res.text()
  let body: unknown = null
  try { body = text ? JSON.parse(text) : null } catch { body = { error: 'invalid_json', detail: text.slice(0, 200) } }
  if (!res.ok) throw new SutraApiError(res.status, (body || {}) as Partial<ApiError>)
  return body as T
}

export const get = <T,>(path: string) => request<T>(path)
export const post = <T,>(path: string, body: unknown) => request<T>(path, { method: 'POST', body: JSON.stringify(body) })
export const patch = <T,>(path: string, body: unknown) => request<T>(path, { method: 'PATCH', body: JSON.stringify(body) })
