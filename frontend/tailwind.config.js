const c = (v) => `rgb(var(--${v}) / <alpha-value>)`

/** @type {import('tailwindcss').Config} */
export default {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        page: c('page'), surface: c('surface'), ink: c('ink'), muted: c('muted'),
        line: c('line'), accent: c('accent'), amber: c('amber'), bad: c('bad'),
      },
      fontFamily: {
        display: ['"Iowan Old Style"', '"Palatino Linotype"', 'Palatino', 'Georgia', 'serif'],
        sans: ['"Avenir Next"', '"Segoe UI"', 'system-ui', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}
