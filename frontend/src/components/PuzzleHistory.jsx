import { useEffect, useState } from 'react'
import { api } from '../api/client.js'

export default function PuzzleHistory({ refreshKey, onLoad }) {
  const [runs, setRuns] = useState([])
  const [err, setErr] = useState(null)

  useEffect(() => {
    api.runs().then((r) => { setRuns(r); setErr(null) }).catch((e) => setErr(e.message))
  }, [refreshKey])

  return (
    <section className="panel" aria-label="Run history">
      <h2 className="font-display text-xl">Run history</h2>
      {err && <p className="mt-2 text-sm text-bad">History unavailable: {err}</p>}
      {!err && runs.length === 0 && <p className="mt-2 text-sm text-muted">No runs yet. Solve a puzzle and it will be saved here.</p>}
      <ul className="mt-2 max-h-52 divide-y divide-line overflow-y-auto text-sm">
        {runs.map((r) => (
          <li key={r.id}>
            <button type="button" className="flex w-full items-center justify-between gap-2 py-1.5 text-left hover:text-accent" onClick={() => onLoad(r.id)}>
              <span>#{r.id} {r.method}</span>
              <span className="text-muted">{r.status} · {r.duration_ms != null ? `${Math.round(r.duration_ms)} ms` : '–'}</span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}
