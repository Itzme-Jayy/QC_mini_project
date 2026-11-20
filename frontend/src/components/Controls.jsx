export default function Controls({ options, setOptions, busy, boardSize = 9, onBoardSizeChange, onGenerate, onSolve, onClearAll, onClearEntries, onKey }) {
  const set = (k) => (e) => setOptions((o) => ({ ...o, [k]: e.target.type === 'checkbox' ? e.target.checked : Number(e.target.value) }))
  const disabled = !!busy
  const is4x4 = boardSize === 4
  const digits = is4x4 ? [1, 2, 3, 4] : [1, 2, 3, 4, 5, 6, 7, 8, 9]

  return (
    <section aria-label="Controls" className="panel space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-2 border-b border-line pb-3">
        <span className="text-sm font-medium">Board Size:</span>
        <div className="flex gap-2">
          <button
            type="button"
            className={`btn py-1 text-sm ${is4x4 ? 'btn-primary' : ''}`}
            disabled={disabled}
            onClick={() => onBoardSizeChange?.(4)}
          >
            4×4 (Mini)
          </button>
          <button
            type="button"
            className={`btn py-1 text-sm ${!is4x4 ? 'btn-primary' : ''}`}
            disabled={disabled}
            onClick={() => onBoardSizeChange?.(9)}
          >
            9×9 (Standard)
          </button>
        </div>
      </div>

      <div className={`grid ${is4x4 ? 'grid-cols-4 max-w-[16rem]' : 'grid-cols-9 sm:max-w-[34rem]'} gap-1`}>
        {digits.map((d) => (
          <button key={d} type="button" className="btn px-0 font-display text-base" onClick={() => onKey(d)} aria-label={`Enter ${d}`}>{d}</button>
        ))}
      </div>

      <div className="flex flex-wrap gap-2">
        <button type="button" className="btn btn-primary" disabled={disabled} onClick={() => onSolve('quantum')}>
          {busy === 'quantum' ? 'Running Grover…' : 'Solve with quantum'}
        </button>
        <button type="button" className="btn" disabled={disabled} onClick={() => onSolve('classical')}>
          {busy === 'classical' ? 'Solving…' : 'Solve classically'}
        </button>
        <button type="button" className="btn" disabled={disabled} onClick={() => onSolve('compare')}>
          {busy === 'compare' ? 'Comparing…' : 'Compare both'}
        </button>
        <button type="button" className="btn" disabled={disabled} onClick={onClearEntries}>Clear my entries</button>
        <button type="button" className="btn" disabled={disabled} onClick={onClearAll}>Clear all</button>
      </div>

      <div className="grid grid-cols-2 gap-3 text-sm sm:grid-cols-4">
        <label className="flex flex-col gap-1">Clues to generate
          <input
            type="number"
            min={is4x4 ? '4' : '22'}
            max={is4x4 ? '14' : '80'}
            value={options.clues}
            onChange={set('clues')}
            className="rounded-md border border-line bg-page px-2 py-1"
          />
        </label>
        <label className="flex flex-col gap-1">Qubit budget
          <input type="number" min="8" max="24" value={options.qubit_budget} onChange={set('qubit_budget')} className="rounded-md border border-line bg-page px-2 py-1" />
        </label>
        <label className="flex flex-col gap-1">Shots per run
          <input type="number" min="1" max="4096" value={options.shots} onChange={set('shots')} className="rounded-md border border-line bg-page px-2 py-1" />
        </label>
        <label className="flex items-end gap-2 pb-1">
          <input type="checkbox" checked={options.propagation} onChange={set('propagation')} />
          Use singles propagation
        </label>
      </div>

      <button type="button" className="btn" disabled={disabled} onClick={onGenerate}>
        {busy === 'generate' ? 'Generating…' : `Generate a random ${is4x4 ? '4×4' : '9×9'} puzzle`}
      </button>
    </section>
  )
}
