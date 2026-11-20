import { cellName, getGridSize } from '../utils/sudoku.js'

export default function SudokuGrid({ values, locked, solution, conflicts, windowCells, selected, onSelect, onChange }) {
  const size = getGridSize(values)
  const boxDim = Math.floor(Math.sqrt(size))

  const handleKey = (e) => {
    if (selected == null) return
    const row = Math.floor(selected / size), col = selected % size
    if (e.key === 'ArrowUp') {
      e.preventDefault()
      if (row > 0) onSelect(selected - size)
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      if (row < size - 1) onSelect(selected + size)
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault()
      if (col > 0) onSelect(selected - 1)
    } else if (e.key === 'ArrowRight') {
      e.preventDefault()
      if (col < size - 1) onSelect(selected + 1)
    } else if (size === 4 && /^[1-4]$/.test(e.key)) {
      onChange(selected, Number(e.key))
    } else if (size === 9 && /^[1-9]$/.test(e.key)) {
      onChange(selected, Number(e.key))
    } else if (['0', 'Backspace', 'Delete', ' '].includes(e.key)) {
      e.preventDefault()
      onChange(selected, 0)
    }
  }

  const gridClass = size === 4
    ? 'grid aspect-square w-full max-w-[20rem] grid-cols-4 overflow-hidden rounded-lg border-2 border-ink/70 bg-surface select-none mx-auto'
    : 'grid aspect-square w-full max-w-[34rem] grid-cols-9 overflow-hidden rounded-lg border-2 border-ink/70 bg-surface select-none'

  return (
    <div role="grid" aria-label="Sudoku grid" tabIndex={0} onKeyDown={handleKey} className={gridClass}>
      {values.map((v, i) => {
        const r = Math.floor(i / size), c = i % size
        const shown = v || solution?.[i] || 0
        const isSolved = !v && !!solution?.[i]
        const given = !isSolved && !!v && locked.has(i)
        const bad = conflicts.has(i)
        const inWindow = windowCells.has(i)
        const isRightBox = c < size - 1 && c % boxDim === boxDim - 1
        const isBottomBox = r < size - 1 && r % boxDim === boxDim - 1
        const cls = [
          'relative flex items-center justify-center font-display leading-none cursor-pointer border-line',
          size === 4 ? 'text-[clamp(1.5rem,6vw,2.5rem)]' : 'text-[clamp(1.1rem,4.4vw,1.9rem)]',
          c < size - 1 ? (isRightBox ? 'border-r-2 border-r-ink/60' : 'border-r') : '',
          r < size - 1 ? (isBottomBox ? 'border-b-2 border-b-ink/60' : 'border-b') : '',
          bad ? 'bg-bad/20 text-bad' : inWindow ? 'bg-amber/25' : '',
          given ? 'font-bold' : v ? 'text-accent' : isSolved ? 'text-muted italic' : '',
          selected === i ? 'outline outline-2 -outline-offset-2 outline-accent z-10' : '',
        ].join(' ')
        return (
          <div key={i} role="gridcell" data-testid={`cell-${i}`} data-conflict={bad ? 'true' : 'false'}
            data-window={inWindow ? 'true' : 'false'} aria-selected={selected === i}
            aria-label={`${cellName(i, size)}: ${shown || 'empty'}`} className={cls} onClick={() => onSelect(i)}>
            {shown || ''}
          </div>
        )
      })}
    </div>
  )
}
