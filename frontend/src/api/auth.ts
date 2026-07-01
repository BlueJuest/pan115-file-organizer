import { apiGet, apiSend } from './client'

export interface AuthUser {
  username: string
}

export function login(username: string, password: string): Promise<AuthUser> {
  return apiSend<AuthUser>('/api/auth/login', 'POST', { username, password })
}

export function getCurrentUser(): Promise<AuthUser> {
  return apiGet<AuthUser>('/api/auth/me')
}

export function logout(): Promise<{ status: string }> {
  return apiSend<{ status: string }>('/api/auth/logout', 'POST')
}
