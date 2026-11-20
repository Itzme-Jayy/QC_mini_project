import { fireEvent, render, screen } from '@testing-library/react'
import { useState } from 'react'
import { describe, expect, it } from 'vitest'
import CircuitView from '../components/CircuitView.jsx'
import ProbabilityChart from '../components/ProbabilityChart.jsx'
import StepExplainer from '../components/StepExplainer.jsx'

const trace = [
  { index: 0, type: 'propagation', description: 'Propagation filled 3 cells.', payload: {} },
  { index: 1, type: 'window', description: 'Quantum window of 2 cells.', payload: { n: 3 } },
  { index: 2, type: 'measurement', description: 'BBHT search ran 1 attempt.',
    payload: { N: 8, valid_count: 2, iterations: 1, optimal_iterations: 1, success_probability: 0.9 } },
]
const outcome = (bits, p, valid) => ({ bits, p, valid, digits: [Number(bits[0]) + 1, 3] })
const chartData = {
  N: 8, valid_count: 2, iterations: 1, success_probability: 0.9, note: null,
  before: [outcome('000', 0.125, true), outcome('001', 0.125, false)],
  after: [outcome('000', 0.45, true), outcome('001', 0.05, false)],
}
const circuit = {
  n_data: 2, iterations: 2,
  wires: [{ index: 0, kind: 'data', label: 'r1c1[0]' }, { index: 1, kind: 'data', label: 'r1c1[1]' }, { index: 2, kind: 'ancilla', label: 'flag' }],
  sections: {
    superposition: [{ op: 'h', qubits: [0] }, { op: 'h', qubits: [1] }],
    oracle: [{ op: 'mcx', controls: [0, 1], target: 2 }],
    diffusion: [{ op: 'z', qubits: [0] }],
  },
}

function Harness() {
  const [i, setI] = useState(0)
  return <StepExplainer trace={trace} index={i} setIndex={setI} />
}

describe('trace views', () => {
  it('steps through the trace', () => {
    render(<Harness />)
    expect(screen.getByTestId('step-description')).toHaveTextContent('Propagation filled 3 cells.')
    fireEvent.click(screen.getByRole('button', { name: 'Next' }))
    expect(screen.getByTestId('step-description')).toHaveTextContent('Quantum window of 2 cells.')
    fireEvent.click(screen.getByRole('button', { name: 'Previous' }))
    expect(screen.getByText('Step 1 of 3')).toBeInTheDocument()
  })

  it('shows Grover formulas on the measurement step', () => {
    render(<StepExplainer trace={trace} index={2} setIndex={() => {}} />)
    expect(screen.getByText(/sin²\(\(2k\+1\)θ\)/)).toBeInTheDocument()
    expect(screen.getByText(/N = 8, M = 2/)).toBeInTheDocument()
  })

  it('renders probability summary and outcome list', () => {
    render(<ProbabilityChart data={chartData} />)
    expect(screen.getByText('Before amplification (uniform)')).toBeInTheDocument()
    expect(screen.getByText('After amplification')).toBeInTheDocument()
    expect(screen.getByLabelText('Most likely outcomes')).toHaveTextContent('1·3 — 45.00% (valid)')
  })

  it('renders the circuit and toggles one expanded iteration', () => {
    render(<CircuitView circuit={circuit} />)
    expect(screen.getByRole('img', { name: 'Grover circuit diagram' })).toBeInTheDocument()
    expect(screen.getByText('×2', { selector: 'strong' })).toBeInTheDocument()
    const btn = screen.getByRole('button', { name: 'Expand one iteration' })
    fireEvent.click(btn)
    expect(screen.getByRole('button', { name: 'Collapse iteration' })).toHaveAttribute('aria-expanded', 'true')
  })
})
