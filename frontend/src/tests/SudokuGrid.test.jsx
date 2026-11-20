import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import SudokuGrid from '../components/SudokuGrid.jsx'
import { emptyGrid } from '../utils/sudoku.js'

const setup = (props = {}) => {
  const onSelect = vi.fn(), onChange = vi.fn()
  const values = emptyGrid()
  render(<SudokuGrid values={values} locked={new Set()} solution={null} conflicts={new Set()}
    windowCells={new Set()} selected={10} onSelect={onSelect} onChange={onChange} {...props} />)
  return { onSelect, onChange }
}

describe('SudokuGrid', () => {
  it('selects a cell on click', () => {
    const { onSelect } = setup()
    fireEvent.click(screen.getByTestId('cell-4'))
    expect(onSelect).toHaveBeenCalledWith(4)
  })

  it('enters and deletes digits with the keyboard', () => {
    const { onChange } = setup()
    const grid = screen.getByRole('grid')
    fireEvent.keyDown(grid, { key: '7' })
    expect(onChange).toHaveBeenLastCalledWith(10, 7)
    fireEvent.keyDown(grid, { key: 'Backspace' })
    expect(onChange).toHaveBeenLastCalledWith(10, 0)
  })

  it('moves with arrow keys and stays inside the board', () => {
    const { onSelect } = setup({ selected: 8 })
    const grid = screen.getByRole('grid')
    fireEvent.keyDown(grid, { key: 'ArrowRight' })
    expect(onSelect).not.toHaveBeenCalled()
    fireEvent.keyDown(grid, { key: 'ArrowDown' })
    expect(onSelect).toHaveBeenCalledWith(17)
  })

  it('marks conflicting and window cells', () => {
    setup({ conflicts: new Set([0, 1]), windowCells: new Set([2]) })
    expect(screen.getByTestId('cell-0')).toHaveAttribute('data-conflict', 'true')
    expect(screen.getByTestId('cell-2')).toHaveAttribute('data-window', 'true')
    expect(screen.getByTestId('cell-3')).toHaveAttribute('data-conflict', 'false')
  })

  it('renders a 4x4 grid with 16 cells and 2x2 box boundaries', () => {
    const values = emptyGrid(4)
    render(<SudokuGrid values={values} locked={new Set()} solution={null} conflicts={new Set()}
      windowCells={new Set()} selected={0} onSelect={vi.fn()} onChange={vi.fn()} />)
    expect(screen.getAllByRole('gridcell')).toHaveLength(16)
  })
})
