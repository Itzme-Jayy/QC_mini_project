import { useCallback, useState } from 'react'
import { api } from '../api/client.js'
import { emptyGrid } from '../utils/sudoku.js'

export function useSolver() {
  const [boardSize, setBoardSize] = useState(9)
  const [values, setValues] = useState(() => emptyGrid(9))
  const [locked, setLocked] = useState(() => new Set())
  const [busy, setBusy] = useState(null)
  const [error, setError] = useState(null)
  const [quantum, setQuantum] = useState(null)
  const [classical, setClassical] = useState(null)
  const [summary, setSummary] = useState(null)
  const [options, setOptions] = useState({ qubit_budget: 16, shots: 64, propagation: true, clues: 32 })
  const [historyKey, setHistoryKey] = useState(0)

  const resetResults = () => { setQuantum(null); setClassical(null); setSummary(null); setError(null) }

  const changeBoardSize = useCallback((newSize) => {
    if (newSize === boardSize) return
    setBoardSize(newSize)
    setValues(emptyGrid(newSize))
    setLocked(new Set())
    setOptions((o) => ({
      ...o,
      clues: newSize === 4 ? 6 : 32,
    }))
    resetResults()
  }, [boardSize])

  const setCell = useCallback((i, v) => {
    if (locked.has(i)) return
    setValues((prev) => prev.map((x, k) => (k === i ? v : x)))
    resetResults()
  }, [locked])

  const clearAll = useCallback(() => { setValues(emptyGrid(boardSize)); setLocked(new Set()); resetResults() }, [boardSize])
  const clearEntries = useCallback(() => {
    setValues((prev) => prev.map((x, k) => (locked.has(k) ? x : 0)))
    resetResults()
  }, [locked])

  const generate = useCallback(async () => {
    setBusy('generate'); setError(null)
    try {
      const p = await api.generate(options.clues, boardSize)
      setValues(p.grid)
      setLocked(new Set(p.grid.flatMap((v, i) => (v ? [i] : []))))
      resetResults()
    } catch (e) { setError(e.message) } finally { setBusy(null) }
  }, [options.clues, boardSize])

  const solve = useCallback(async (kind) => {
    setBusy(kind); setError(null)
    const body = { grid: values, qubit_budget: options.qubit_budget, shots: options.shots, propagation: options.propagation }
    try {
      if (kind === 'quantum') { setQuantum(await api.solveQuantum(body)); setSummary(null) }
      else if (kind === 'classical') { setClassical(await api.solveClassical(body)) }
      else {
        const r = await api.compare(body)
        setQuantum(r.quantum); setClassical(r.classical); setSummary(r.summary)
      }
      setHistoryKey((k) => k + 1)
    } catch (e) { setError(e.message) } finally { setBusy(null) }
  }, [values, options])

  const loadRun = useCallback(async (id) => {
    setBusy('load'); setError(null)
    try {
      const run = await api.run(id)
      const pz = [...run.puzzle].map(Number)
      const size = pz.length === 16 ? 4 : 9
      setBoardSize(size)
      setValues(pz)
      setLocked(new Set())
      const solution = run.solved_grid ? [...run.solved_grid].map(Number) : null
      const base = { run_id: run.id, method: run.method, status: run.status, solution,
        metrics: { time_ms: run.duration_ms, max_qubits: run.qubits_used, iterations: run.grover_iterations,
          backtracks: run.backtracks, nodes: run.nodes_explored } }
      if (run.method === 'quantum') { setQuantum({ ...base, trace: run.trace }); setClassical(null) }
      else { setClassical(base); setQuantum(null) }
      setSummary(null)
    } catch (e) { setError(e.message) } finally { setBusy(null) }
  }, [])

  return { boardSize, changeBoardSize, values, locked, busy, error, quantum, classical, summary, options, setOptions, historyKey,
    setCell, clearAll, clearEntries, generate, solve, loadRun }
}
