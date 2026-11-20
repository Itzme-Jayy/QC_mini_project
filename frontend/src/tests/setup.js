import '@testing-library/jest-dom/vitest'
import { afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'

if (typeof globalThis.localStorage === 'undefined' || !globalThis.localStorage?.clear) {
  const store = new Map()
  const mockStorage = {
    getItem: (k) => (store.has(k) ? store.get(k) : null),
    setItem: (k, v) => store.set(k, String(v)),
    removeItem: (k) => store.delete(k),
    clear: () => store.clear(),
    key: (i) => Array.from(store.keys())[i] || null,
    get length() {
      return store.size
    },
  }
  Object.defineProperty(globalThis, 'localStorage', {
    value: mockStorage,
    writable: true,
    configurable: true,
  })
}

afterEach(() => { cleanup(); localStorage.clear(); document.documentElement.classList.remove('dark') })

// Recharts measures its container; jsdom has no layout engine.
globalThis.ResizeObserver = class { observe() {} unobserve() {} disconnect() {} }
