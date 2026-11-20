export const emptyGrid = (size = 9) => Array(size * size).fill(0)

export const getGridSize = (values) => {
  const len = values?.length || 81
  return len === 16 ? 4 : 9
}

export const rowOf = (i, size = 9) => Math.floor(i / size)
export const colOf = (i, size = 9) => i % size
export const boxOf = (i, size = 9) => {
  const dim = Math.floor(Math.sqrt(size))
  return Math.floor(rowOf(i, size) / dim) * dim + Math.floor(colOf(i, size) / dim)
}

export function arePeers(a, b, size = 9) {
  return a !== b && (rowOf(a, size) === rowOf(b, size) || colOf(a, size) === colOf(b, size) || boxOf(a, size) === boxOf(b, size))
}

/** Set of cell indices that share a row, column or box with another cell holding the same digit. */
export function findConflicts(values) {
  const size = getGridSize(values)
  const total = size * size
  const bad = new Set()
  for (let i = 0; i < total; i++) {
    if (!values[i]) continue
    for (let j = i + 1; j < total; j++) {
      if (values[j] === values[i] && arePeers(i, j, size)) {
        bad.add(i)
        bad.add(j)
      }
    }
  }
  return bad
}

export const cellName = (i, size = 9) => `row ${rowOf(i, size) + 1}, column ${colOf(i, size) + 1}`
export const cellShort = (i, size = 9) => `r${rowOf(i, size) + 1}c${colOf(i, size) + 1}`
