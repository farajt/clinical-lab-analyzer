import { useState } from 'react'
import Papa from 'papaparse'

const EMPTY_ROW = { test_name: '', value: '', unit: '' }

export default function LabInput({ onSubmit, loading }) {
  const [mode, setMode] = useState('form')
  const [rows, setRows] = useState([{ ...EMPTY_ROW }])
  const [csvLabs, setCsvLabs] = useState(null)
  const [csvFileName, setCsvFileName] = useState('')
  const [parseError, setParseError] = useState('')

  function updateRow(i, field, value) {
    const next = [...rows]
    next[i] = { ...next[i], [field]: value }
    setRows(next)
  }

  function addRow() {
    setRows([...rows, { ...EMPTY_ROW }])
  }

  function removeRow(i) {
    setRows(rows.filter((_, idx) => idx !== i))
  }

  function handleFile(e) {
    const file = e.target.files[0]
    if (!file) return

    setCsvFileName(file.name)
    setParseError('')
    setCsvLabs(null)

    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,

      complete: (results) => {
        try {
          const labs = results.data.map((r) => {
            const raw =
              r.value ??
              r.Value ??
              r.Result ??
              r.result

            const isBlank =
              raw === undefined ||
              raw === null ||
              String(raw).trim() === ''

            const rawValue = isBlank
              ? null
              : String(raw).trim()

            // Preserve numeric values as numbers.
            // Preserve qualitative values such as:
            // "Normal", "Negatif", "1+" as strings.
            let parsedValue = null

            if (!isBlank) {
              const numericValue = Number(rawValue)

              parsedValue =
                rawValue !== '' && Number.isFinite(numericValue)
                  ? numericValue
                  : rawValue
            }

            const minRef =
              r.min_reference ??
              r.Min_Reference

            const maxRef =
              r.max_reference ??
              r.Max_Reference

            const refBlank = (v) =>
              v === undefined ||
              v === null ||
              String(v).trim() === ''

            const parsedMinRef = refBlank(minRef)
              ? null
              : Number(minRef)

            const parsedMaxRef = refBlank(maxRef)
              ? null
              : Number(maxRef)

            return {
              test_name:
                r.test_name ??
                r.Test ??
                r.test ??
                r.Test_Name ??
                '',

              value: parsedValue,

              unit:
                r.unit ??
                r.Unit ??
                '',

              min_reference:
                Number.isFinite(parsedMinRef)
                  ? parsedMinRef
                  : null,

              max_reference:
                Number.isFinite(parsedMaxRef)
                  ? parsedMaxRef
                  : null,
            }
          })

          setCsvLabs(labs)
        } catch (err) {
          setParseError(
            'Could not read CSV. Expected columns: test_name, value, unit'
          )
        }
      },

      error: () =>
        setParseError('Failed to parse CSV file'),
    })
  }

  function submit() {
    if (mode === 'csv') {
      if (!csvLabs || csvLabs.length === 0) {
        setParseError('Upload a CSV first')
        return
      }

      onSubmit(csvLabs)
    } else {
      const labs = rows
        .filter(
          (r) => r.test_name.trim() !== ''
        )
        .map((r) => ({
          test_name: r.test_name,
          value: Number(r.value),
          unit: r.unit,
        }))

      onSubmit(labs)
    }
  }

  return (
    <section className="input-panel">

      <div className="input-panel-header">
        <div>
          <div className="eyebrow">LAB DATA</div>

          <h2>Enter laboratory results</h2>

          <p>
            Add individual test results manually or upload
            a CSV containing multiple laboratory measurements.
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="input-tabs">
        <button
          className={`input-tab ${
            mode === 'form' ? 'active' : ''
          }`}
          onClick={() => setMode('form')}
          type="button"
        >
          <span>✎</span>
          Manual entry
        </button>

        <button
          className={`input-tab ${
            mode === 'csv' ? 'active' : ''
          }`}
          onClick={() => setMode('csv')}
          type="button"
        >
          <span>↑</span>
          Upload CSV
        </button>
      </div>

      {/* Manual */}
      {mode === 'form' ? (
        <div className="manual-area">

          <div className="form-labels">
            <span>Test name</span>
            <span>Value</span>
            <span>Unit</span>
            <span></span>
          </div>

          {rows.map((row, i) => (
            <div
              key={i}
              className="lab-input-row"
            >
              <input
                placeholder="e.g. Hemoglobin"
                value={row.test_name}
                onChange={(e) =>
                  updateRow(
                    i,
                    'test_name',
                    e.target.value
                  )
                }
                className="lab-input test-name-input"
              />

              <input
                placeholder="Value"
                type="number"
                value={row.value}
                onChange={(e) =>
                  updateRow(
                    i,
                    'value',
                    e.target.value
                  )
                }
                className="lab-input value-input"
              />

              <input
                placeholder="e.g. g/dL"
                value={row.unit}
                onChange={(e) =>
                  updateRow(
                    i,
                    'unit',
                    e.target.value
                  )
                }
                className="lab-input unit-input"
              />

              {rows.length > 1 ? (
                <button
                  type="button"
                  onClick={() => removeRow(i)}
                  className="remove-row-button"
                  aria-label="Remove row"
                >
                  ×
                </button>
              ) : (
                <span className="remove-placeholder"></span>
              )}
            </div>
          ))}

          <button
            type="button"
            onClick={addRow}
            className="add-test-button"
          >
            <span>+</span>
            Add another test
          </button>
        </div>
      ) : (
        /* CSV */
        <div className="csv-area">

          <label className="csv-dropzone">
            <div className="upload-icon">↑</div>

            <strong>
              {csvFileName || 'Choose a CSV file'}
            </strong>

            <span>
              {csvFileName
                ? 'Click to choose a different file'
                : 'Supports laboratory result CSV files'}
            </span>

            <input
              type="file"
              accept=".csv"
              onChange={handleFile}
              style={{ display: 'none' }}
            />
          </label>

          {csvLabs && (
            <div className="csv-success">
              <span className="csv-success-icon">✓</span>

              <div>
                <strong>CSV loaded successfully</strong>
                <span>
                  {csvLabs.length} laboratory result
                  {csvLabs.length !== 1 ? 's' : ''} ready
                  for analysis
                </span>
              </div>
            </div>
          )}

          {parseError && (
            <div className="csv-error">
              <span>!</span>
              {parseError}
            </div>
          )}
        </div>
      )}

      {/* Analyze */}
      <div className="analyze-area">
        <button
          onClick={submit}
          disabled={loading}
          className="analyze-button"
          type="button"
        >
          {loading ? (
            <>
              <span className="loading-spinner"></span>
              Analyzing results…
            </>
          ) : (
            <>
              Analyze results
              <span className="button-arrow">→</span>
            </>
          )}
        </button>

        <p className="analyze-note">
          Results are classified by severity and explained
          using AI.
        </p>
      </div>
    </section>
  )
}