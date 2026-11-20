import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import ThemeToggle from '../components/ThemeToggle.jsx'
import { ThemeProvider } from '../context/ThemeContext.jsx'

const mount = () => render(<ThemeProvider><ThemeToggle /></ThemeProvider>)

describe('theme toggle', () => {
  it('switches the dark class and persists the choice', () => {
    mount()
    const btn = screen.getByRole('button')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
    fireEvent.click(btn)
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(localStorage.getItem('qs-theme')).toBe('dark')
  })

  it('restores the saved theme on load', () => {
    localStorage.setItem('qs-theme', 'dark')
    mount()
    expect(document.documentElement.classList.contains('dark')).toBe(true)
    expect(screen.getByRole('button')).toHaveAttribute('aria-pressed', 'true')
  })
})
