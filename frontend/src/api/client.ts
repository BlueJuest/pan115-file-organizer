export async function apiGet<T>(url: string): Promise<T> {
  const response = await fetch(url)
  if (!response.ok) throw new Error(await response.text())
  return response.json() as Promise<T>
}

export async function apiSend<T>(url: string, method: 'POST' | 'PUT' | 'DELETE', body?: unknown): Promise<T> {
  const response = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!response.ok) throw new Error(await response.text())
  return response.json() as Promise<T>
}
