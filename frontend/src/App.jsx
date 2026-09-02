import { useState } from 'react'
import LabInput from './components/LabInput'
import ResultsDisplay from './components/ResultsDisplay'
import { analyzeLabs } from './api'

export default function App() {
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(labs) {
    setLoading(true)
    setError('')
    setResults(null)

    try {
      const data = await analyzeLabs(labs)
      setResults(data)
    } catch (err) {
      setError(err.message || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app-shell">
      <div className="app-container">

        {/* Header */}
        <header className="app-header">
          <div className="brand-mark">
            <span className="brand-icon">+</span>
          </div>

          <div>
            <div className="eyebrow">AI-ASSISTED CLINICAL ANALYSIS</div>
            <h1>Clinical Lab Results Analyzer</h1>
            <p>
              Analyze laboratory results, identify potential abnormalities,
              and understand what they mean through explainable AI.
            </p>
          </div>
        </header>

        {/* Main input */}
        <main>
          <LabInput
            onSubmit={handleSubmit}
            loading={loading}
          />

          {/* API error */}
          {error && (
            <div className="app-error">
              <div className="error-icon">!</div>
              <div>
                <strong>Analysis could not be completed</strong>
                <p>{error}</p>
              </div>
            </div>
          )}

          {/* Results */}
          <ResultsDisplay results={results} />
        </main>

        {/* Footer */}
        <footer className="app-footer">
          <span>Clinical Lab Results Analyzer</span>
          <span>•</span>
          <span>Explainable AI</span>
          <span>•</span>
          <span>FastAPI + MCP + React</span>
        </footer>

      </div>
    </div>
  )
}