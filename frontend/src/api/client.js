const BASE = import.meta.env.VITE_API_URL || '/api'

async function request(path, options = {}) {
  let res
  try {
    res = await fetch(`${BASE}${path}`, { headers: { 'Content-Type': 'application/json' }, ...options })
  } catch {
    throw new Error('Cannot reach the API. Is the Flask server running on port 5001?')
  }
  let data = null
  try { data = await res.json() } catch { /* empty body */ }
  if (!res.ok) throw new Error(data?.error || `Request failed (${res.status})`)
  return data
}

const post = (path, body) => request(path, { method: 'POST', body: JSON.stringify(body) })

export const api = {
  generate: (clues, size = 9) => post('/puzzles/generate', { clues, size }),
  solveQuantum: (body) => post('/solve/quantum', body),
  solveClassical: (body) => post('/solve/classical', body),
  compare: (body) => post('/solve/compare', body),
  runs: () => request('/runs'),
  run: (id) => request(`/runs/${id}`),
}
