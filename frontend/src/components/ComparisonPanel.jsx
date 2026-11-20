const fmtMs = (v) => (v == null ? '–' : v < 1000 ? `${v.toFixed(1)} ms` : `${(v / 1000).toFixed(2)} s`)
const dash = (v) => (v == null ? '–' : v)

export default function ComparisonPanel({ quantum, classical, summary }) {
  if (!quantum && !classical) {
    return <section className="panel"><h2 className="font-display text-xl">Classical vs quantum</h2>
      <p className="mt-2 text-sm text-muted">Run “Compare both” to see the two solvers side by side.</p></section>
  }
  const rows = [
    ['Status', classical?.status, quantum?.status],
    ['Time', fmtMs(classical?.metrics?.time_ms), fmtMs(quantum?.metrics?.time_ms)],
    ['Nodes explored', dash(classical?.metrics?.nodes), '–'],
    ['Backtracks', dash(classical?.metrics?.backtracks), dash(quantum?.metrics?.backtracks)],
    ['Qubits (largest circuit)', '–', dash(quantum?.metrics?.max_qubits)],
    ['Grover iterations', '–', dash(quantum?.metrics?.iterations)],
    ['Quantum windows', '–', dash(quantum?.metrics?.windows)],
    ['Simulator runs', '–', dash(quantum?.metrics?.simulations)],
  ]
  return (
    <section className="panel" aria-label="Classical versus quantum comparison">
      <h2 className="font-display text-xl">Classical vs quantum</h2>
      <div className="mt-3 overflow-x-auto">
        <div className="grid min-w-[22rem] grid-cols-[1.6fr_1fr_1fr] text-sm">
          <div /><div className="pb-2 font-semibold">Backtracking (MRV)</div><div className="pb-2 font-semibold">Hybrid Grover</div>
          {rows.map(([label, a, b]) => (
            <div key={label} className="contents">
              <div className="border-t border-line py-1.5 text-muted">{label}</div>
              <div className="border-t border-line py-1.5">{a ?? '–'}</div>
              <div className="border-t border-line py-1.5">{b ?? '–'}</div>
            </div>
          ))}
        </div>
      </div>
      {summary && (
        <p className="mt-3 text-sm leading-relaxed text-muted">
          {summary.slowdown ? `The simulated quantum run took ${summary.slowdown.toFixed(1)}× as long. ` : ''}{summary.note}
        </p>
      )}
    </section>
  )
}
