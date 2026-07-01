export async function apiGet<T>(url: string): Promise<T> {
  const response = await fetch(url, { credentials: 'include' })
  if (!response.ok) throw new Error(await readErrorMessage(response))
  return response.json() as Promise<T>
}

export async function apiSend<T>(url: string, method: 'POST' | 'PUT' | 'DELETE', body?: unknown): Promise<T> {
  const response = await fetch(url, {
    method,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!response.ok) throw new Error(await readErrorMessage(response))
  return response.json() as Promise<T>
}

async function readErrorMessage(response: Response): Promise<string> {
  const text = await response.text()
  if (!text) return `请求失败：HTTP ${response.status}`
  try {
    const payload = JSON.parse(text) as { detail?: unknown; message?: unknown }
    if (typeof payload.detail === 'string') return payload.detail
    if (Array.isArray(payload.detail)) return payload.detail.map(formatDetailItem).join('；')
    if (typeof payload.message === 'string') return payload.message
  } catch {
    return text
  }
  return text
}

function formatDetailItem(item: unknown): string {
  if (typeof item === 'string') return item
  if (item && typeof item === 'object') {
    const detail = item as { loc?: unknown[]; msg?: unknown }
    const location = Array.isArray(detail.loc) ? detail.loc.join('.') : ''
    const message = typeof detail.msg === 'string' ? detail.msg : JSON.stringify(item)
    return location ? `${location}: ${message}` : message
  }
  return String(item)
}
