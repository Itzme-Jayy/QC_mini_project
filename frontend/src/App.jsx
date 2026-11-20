import { useEffect, useMemo, useState } from 'react'
import CircuitView from './components/CircuitView.jsx'
import ComparisonPanel from './components/ComparisonPanel.jsx'
import Controls from './components/Controls.jsx'
import ProbabilityChart from './components/ProbabilityChart.jsx'
import PuzzleHistory from './components/PuzzleHistory.jsx'
import StepExplainer from './components/StepExplainer.jsx'
import SudokuGrid from './components/SudokuGrid.jsx'
import ThemeToggle from './components/ThemeToggle.jsx'
import { useSolver } from './hooks/useSolver.js'
import { findConflicts } from './utils/sudoku.js'

export default function App() {
  const s = useSolver()
  const [selected, setSelected] = useState(0)
  const [stepIdx, setStepIdx] = useState(0)

  const trace = s.quantum?.trace || []
  useEffect(() => { setStepIdx(Math.max(0, trace.length - 1)) }, [s.quantum])

  const conflicts = useMemo(() => findConflicts(s.values), [s.values])
  const step = trace[stepIdx]
  const upTo = trace.slice(0, stepIdx + 1)
  const snapshot = trace.length ? [...upTo].reverse().find((t) => t.payload?.grid)?.payload.grid : null
  const solution = trace.length ? snapshot : (s.quantum?.solution || s.classical?.solution || null)
  const windowCells = new Set(step?.payload?.window_cells || [])

  const activeWindow = step?.payload?.window_id ?? [...upTo].reverse().find((t) => t.payload?.window_id != null)?.payload.window_id
  const circuit = trace.find((t) => t.payload?.window_id === activeWindow && t.payload?.circuit)?.payload.circuit
  const measurement = trace.find((t) => t.type === 'measurement' && t.payload?.window_id === activeWindow && t.payload?.before)?.payload

  return (
    <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6">
      <header className="mb-6 flex flex-wrap items-start justify-between gap-4">
        <div className="max-w-2xl">
          <h1 className="font-display text-3xl font-semibold tracking-tight sm:text-4xl">Quantum Sudoku Solver</h1>
          <p className="mt-2 text-sm leading-relaxed text-muted">
            Sudoku boards are too large for one all-at-once Grover circuit on a simulator, so the solver works in small windows:
            propagate, search a window with Grover, verify classically, commit, repeat. Supports both 4×4 and 9×9 boards on a local Qiskit Aer simulator.
          </p>
        </div>
        <ThemeToggle />
      </header>

      {s.error && <div role="alert" className="mb-4 rounded-md border border-bad bg-bad/10 px-3 py-2 text-sm text-bad">{s.error}</div>}
      {s.busy && s.busy !== 'generate' && <div role="status" className="mb-4 text-sm text-muted">Working… quantum solves can take several seconds on a simulator.</div>}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,36rem)_minmax(0,1fr)]">
        <div className="space-y-4">
          <SudokuGrid values={s.values} locked={s.locked} solution={solution} conflicts={conflicts}
            windowCells={windowCells} selected={selected} onSelect={setSelected} onChange={s.setCell} />
          {conflicts.size > 0 && <p className="text-sm text-bad">Highlighted cells break a row, column or box rule.</p>}
          <Controls options={s.options} setOptions={s.setOptions} busy={s.busy} boardSize={s.boardSize}
            onBoardSizeChange={s.changeBoardSize} onGenerate={s.generate}
            onSolve={s.solve} onClearAll={s.clearAll} onClearEntries={s.clearEntries} onKey={(d) => s.setCell(selected, d)} />
        </div>
        <div className="space-y-4">
          <ComparisonPanel quantum={s.quantum} classical={s.classical} summary={s.summary} />
          <StepExplainer trace={trace} index={stepIdx} setIndex={setStepIdx} boardSize={s.boardSize} />
          <CircuitView circuit={circuit} />
          <ProbabilityChart data={measurement} />
          <PuzzleHistory refreshKey={s.historyKey} onLoad={s.loadRun} />
        </div>
      </div>
    </div>
  )
}
