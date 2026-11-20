import { useMemo, useState } from 'react'

const RH = 24, CW = 30, X0 = 128, PAD = 18

function span(g) {
  const qs = g.op === 'mcx' ? [...g.controls, g.target] : g.qubits
  return [Math.min(...qs), Math.max(...qs)]
}

/** Greedy left-to-right layering: a gate sits in the first column where all wires it crosses are free. */
function layout(gates, nQ) {
  const free = Array(nQ).fill(0)
  const placed = gates.map((g) => {
    const [lo, hi] = span(g)
    let col = 0
    for (let q = lo; q <= hi; q++) col = Math.max(col, free[q])
    for (let q = lo; q <= hi; q++) free[q] = col + 1
    return { g, col }
  })
  return { placed, cols: Math.max(0, ...free) }
}

function Gate({ g, x, y }) {
  if (g.op === 'mcx') {
    const [lo, hi] = span(g)
    return (
      <g>
        <line x1={x} x2={x} y1={y(lo)} y2={y(hi)} className="stroke-ink" strokeWidth="1.2" />
        {g.controls.map((q) => <circle key={q} cx={x} cy={y(q)} r="3.5" className="fill-ink" />)}
        <circle cx={x} cy={y(g.target)} r="8" className="fill-surface stroke-ink" strokeWidth="1.2" />
        <path d={`M${x - 8} ${y(g.target)}H${x + 8}M${x} ${y(g.target) - 8}V${y(g.target) + 8}`} className="stroke-ink" strokeWidth="1.2" />
      </g>
    )
  }
  const q = g.qubits[0]
  return (
    <g>
      <rect x={x - 9} y={y(q) - 9} width="18" height="18" rx="3" className="fill-surface stroke-accent" strokeWidth="1.4" />
      <text x={x} y={y(q) + 4} textAnchor="middle" fontSize="11" className="fill-ink font-mono">{g.op === 'measure' ? 'M' : g.op.toUpperCase()}</text>
    </g>
  )
}

export default function CircuitView({ circuit }) {
  const [expanded, setExpanded] = useState(false)
  const nQ = circuit?.wires?.length || 0

  const segments = useMemo(() => {
    if (!circuit) return []
    const s = circuit.sections
    const segs = [{ title: 'Superposition', gates: s.superposition }]
    if (expanded) {
      segs.push({ title: 'Oracle', gates: s.oracle }, { title: 'Diffusion', gates: s.diffusion })
    } else {
      segs.push({ title: 'Oracle', collapsed: true }, { title: 'Diffusion', collapsed: true })
    }
    segs.push({ title: 'Measure', gates: Array.from({ length: circuit.n_data }, (_, q) => ({ op: 'measure', qubits: [q] })) })
    let x = X0
    return segs.map((seg) => {
      const lay = seg.collapsed ? { placed: [], cols: 3 } : layout(seg.gates, nQ)
      const out = { ...seg, ...lay, x0: x }
      x += lay.cols * CW + PAD
      return out
    })
  }, [circuit, expanded, nQ])

  if (!circuit) {
    return <section className="panel"><h2 className="font-display text-xl">Quantum circuit</h2>
      <p className="mt-2 text-sm text-muted">The circuit for the current window appears here.</p></section>
  }
  const y = (q) => 22 + q * RH
  const height = 34 + nQ * RH
  const width = (segments.at(-1)?.x0 || X0) + (segments.at(-1)?.cols || 1) * CW + PAD
  return (
    <section className="panel" aria-label="Quantum circuit">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="font-display text-xl">Quantum circuit</h2>
        <button type="button" className="btn" onClick={() => setExpanded((e) => !e)} aria-expanded={expanded}>
          {expanded ? 'Collapse iteration' : 'Expand one iteration'}
        </button>
      </div>
      <p className="mt-1 text-sm text-muted">
        {circuit.wires.length} qubits ({circuit.n_data} data, {circuit.wires.length - circuit.n_data} ancilla).
        Oracle and diffusion repeat <strong className="text-ink">×{circuit.iterations}</strong> in the last run.
      </p>
      <div className="mt-3 overflow-x-auto">
        <svg width={width} height={height} role="img" aria-label="Grover circuit diagram">
          {circuit.wires.map((w) => (
            <g key={w.index}>
              <text x="4" y={y(w.index) + 4} fontSize="10" className={w.kind === 'ancilla' ? 'fill-muted' : 'fill-ink'}>{w.label.slice(0, 20)}</text>
              <line x1={X0 - 12} x2={width - 6} y1={y(w.index)} y2={y(w.index)} className="stroke-line" strokeWidth="1" />
            </g>
          ))}
          {segments.map((seg) => (
            <g key={seg.title}>
              <text x={seg.x0} y="11" fontSize="11" className="fill-muted">{seg.title}{seg.collapsed ? ` ×${circuit.iterations}` : ''}</text>
              {seg.collapsed ? (
                <rect x={seg.x0 - 4} y="16" width={seg.cols * CW} height={nQ * RH + 4} rx="4"
                  className="fill-accent/10 stroke-accent" strokeDasharray="4 3" />
              ) : seg.placed.map(({ g, col }, i) => <Gate key={i} g={g} x={seg.x0 + col * CW + CW / 2 - 4} y={y} />)}
            </g>
          ))}
        </svg>
      </div>
    </section>
  )
}
