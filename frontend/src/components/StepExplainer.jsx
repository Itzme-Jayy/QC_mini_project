import { useEffect, useState } from 'react'

const pct = (x) => (x == null ? '–' : `${(x * 100).toFixed(1)}%`)

function formulas(step, boardSize = 9) {
  const p = step.payload || {}
  switch (step.type) {
    case 'propagation':
      return [`candidates(c) = {1…${boardSize}} minus digits already in the row, column and box of c`,
        'hidden single: a digit with exactly one possible cell in a row, column or box']
    case 'window':
      return ['qubits per cell = ⌈log₂ k⌉ for k candidates', `data qubits in this window: n = ${p.n}`]
    case 'superposition':
      return ['|ψ₀⟩ = H^⊗n |0…0⟩ = (1/√N) Σₓ |x⟩', `N = 2^${p.n} = ${p.N}`]
    case 'oracle':
      return ['O|x⟩ = (−1)^f(x) |x⟩, with f(x) = 1 only if x satisfies every constraint',
        `ancilla flags: ${p.flags} · qubits: ${p.qubits} · circuit depth per iteration: ${p.depth_per_iteration}`]
    case 'diffusion':
      return ['D = 2|s⟩⟨s| − I (reflection about the mean amplitude)', 'One Grover iteration = D · O']
    case 'measurement': {
      const out = ['θ = arcsin √(M/N)', 'P(success after k iterations) = sin²((2k+1)θ)', 'k ≈ (π/4) √(N/M)']
      if (p.valid_count) {
        out.push(`here N = ${p.N}, M = ${p.valid_count}, θ-optimal k ≈ ${p.optimal_iterations}, shown k = ${p.iterations}, P = ${pct(p.success_probability)}`)
      }
      return out
    }
    case 'verification':
      return ['accept a measured outcome only if every row, column and box rule holds for it']
    default:
      return []
  }
}

export default function StepExplainer({ trace, index, setIndex, boardSize = 9 }) {
  const [playing, setPlaying] = useState(false)
  const last = trace.length - 1

  useEffect(() => {
    if (!playing) return undefined
    const t = setInterval(() => {
      setIndex((i) => {
        if (i >= last) { setPlaying(false); return i }
        return i + 1
      })
    }, 1100)
    return () => clearInterval(t)
  }, [playing, last, setIndex])

  if (!trace.length) {
    return <section className="panel"><h2 className="font-display text-xl">Step by step</h2>
      <p className="mt-2 text-sm text-muted">Solve with quantum to record the algorithm, then step through it here.</p></section>
  }
  const step = trace[index]
  const lines = formulas(step, boardSize)
  return (
    <section className="panel" aria-label="Algorithm walkthrough">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-display text-xl">Step by step</h2>
        <div className="flex items-center gap-2">
          <button type="button" className="btn" onClick={() => setIndex(Math.max(0, index - 1))} disabled={index === 0}>Previous</button>
          <button type="button" className="btn" onClick={() => setPlaying((p) => !p)}>{playing ? 'Pause' : 'Play'}</button>
          <button type="button" className="btn" onClick={() => setIndex(Math.min(last, index + 1))} disabled={index === last}>Next</button>
        </div>
      </div>
      <input type="range" min="0" max={last} value={index} onChange={(e) => setIndex(Number(e.target.value))}
        className="mt-3 w-full accent-[rgb(var(--accent))]" aria-label="Step position" />
      <p className="mt-1 text-xs text-muted">Step {index + 1} of {trace.length}</p>
      <h3 className="mt-3 text-sm font-semibold capitalize">{step.type}</h3>
      <p className="mt-1 text-sm leading-relaxed" data-testid="step-description">{step.description}</p>
      {lines.length > 0 && (
        <div className="mt-3 space-y-1 rounded-md border border-line bg-page p-3 font-mono text-xs leading-relaxed">
          {lines.map((l) => <div key={l}>{l}</div>)}
        </div>
      )}
    </section>
  )
}
