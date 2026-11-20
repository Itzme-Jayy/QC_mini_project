import { describe, expect, it } from 'vitest'
import { emptyGrid, findConflicts } from '../utils/sudoku.js'

describe('findConflicts', () => {
  it('flags row, column and box clashes only', () => {
    const g = emptyGrid()
    g[0] = 5; g[8] = 5      // same row
    g[40] = 7; g[49] = 7    // same column
    g[3] = 9; g[13] = 4     // different digits
    expect([...findConflicts(g)].sort((a, b) => a - b)).toEqual([0, 8, 40, 49])
  })

  it('flags 4x4 row, column and 2x2 box clashes', () => {
    const g = emptyGrid(4)
    g[0] = 2; g[3] = 2      // same row
    g[1] = 4; g[5] = 4      // same 2x2 box (cells 0, 1, 4, 5)
    expect([...findConflicts(g)].sort((a, b) => a - b)).toEqual([0, 1, 3, 5])
  })
})
