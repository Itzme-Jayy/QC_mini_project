import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

const label = (o) => (o.digits || []).map((d) => d ?? '×').join('·')
const pct = (x) => `${(x * 100).toFixed(2)}%`

function Chart({ title, rows }) {
  const data = rows.map((o) => ({ name: label(o), bits: o.bits, p: o.p, valid: o.valid }))
  return (
    <figure className="min-w-0">
      <figcaption className="mb-1 text-sm font-medium">{title}</figcaption>
      <div className="h-44 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} margin={{ top: 4, right: 4, left: 0, bottom: 0 }}>
            <XAxis dataKey="name" tick={false} axisLine={{ stroke: 'rgb(var(--line))' }} />
            <YAxis tickFormatter={(v) => `${Math.round(v * 100)}%`} width={40} tick={{ fontSize: 11, fill: 'rgb(var(--muted))' }} />
            <Tooltip formatter={(v) => pct(v)} labelFormatter={(l) => `digits ${l}`} />
            <Bar dataKey="p" isAnimationActive={false}>
              {data.map((d) => <Cell key={d.bits} fill={d.valid ? 'rgb(var(--accent))' : 'rgb(var(--muted) / 0.45)'} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </figure>
  )
}

export default function ProbabilityChart({ data }) {
  if (!data) {
    return <section className="panel"><h2 className="font-display text-xl">Measurement probabilities</h2>
      <p className="mt-2 text-sm text-muted">Probabilities appear once a quantum run has a measurement step.</p></section>
  }
  const baseline = data.valid_count ? data.valid_count / data.N : null
  const top = data.after.slice(0, 5)
  return (
    <section className="panel" aria-label="Measurement probabilities">
      <h2 className="font-display text-xl">Measurement probabilities</h2>
      <p className="mt-1 text-sm text-muted">
        Teal bars are valid assignments. Success probability after {data.iterations} iteration(s):{' '}
        <strong className="text-ink">{pct(data.success_probability)}</strong>
        {baseline != null && <> (uniform guess: {pct(baseline)})</>}.
      </p>
      <div className="mt-3 grid gap-4 md:grid-cols-2">
        <Chart title="Before amplification (uniform)" rows={data.before} />
        <Chart title="After amplification" rows={data.after} />
      </div>
      <ul className="mt-3 space-y-0.5 text-xs text-muted" aria-label="Most likely outcomes">
        {top.map((o) => <li key={o.bits}>{label(o)} — {pct(o.p)} {o.valid ? '(valid)' : '(violates a rule)'}</li>)}
      </ul>
      {data.note && <p className="mt-2 text-xs text-muted">{data.note}</p>}
    </section>
  )
}
