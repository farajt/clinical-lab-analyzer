import SeverityBadge from './SeverityBadge'

const SECTIONS = [
  {
    key: 'critical',
    title: 'Critical results',
    description: 'Results that may require prompt clinical attention.',
    icon: '🚨',
    className: 'critical-section',
  },
  {
    key: 'warning',
    title: 'Warning results',
    description: 'Results outside the normal range that may need follow-up.',
    icon: '⚠',
    className: 'warning-section',
  },
  {
    key: 'normal',
    title: 'Normal results',
    description: 'Results within the provided reference ranges.',
    icon: '✓',
    className: 'normal-section',
  },
  {
    key: 'unresolved',
    title: 'Needs attention',
    description: 'Results that could not be automatically classified.',
    icon: '!',
    className: 'unresolved-section',
  },
]

export default function ResultsDisplay({ results }) {
  if (!results) return null

  const critical = results.critical || []
  const warning = results.warning || []
  const normal = results.normal || []
  const unresolved = results.unresolved || []

  const total =
    critical.length +
    warning.length +
    normal.length +
    unresolved.length

  return (
    <div className="results-area">

      {/* Results header */}
      <div className="results-header">
        <div>
          <div className="eyebrow">ANALYSIS COMPLETE</div>
          <h2>Laboratory Results</h2>
          <p>
            Review the classification, reference range, AI interpretation,
            and recommended next steps for each result.
          </p>
        </div>

        <div className="results-total">
          <strong>{total}</strong>
          <span>results</span>
        </div>
      </div>

      {/* Summary */}
      <div className="summary-grid">
        <SummaryCard
          value={critical.length}
          label="Critical"
          icon="🚨"
          className="summary-critical"
        />

        <SummaryCard
          value={warning.length}
          label="Warning"
          icon="⚠"
          className="summary-warning"
        />

        <SummaryCard
          value={normal.length}
          label="Normal"
          icon="✓"
          className="summary-normal"
        />

        <SummaryCard
          value={unresolved.length}
          label="Needs attention"
          icon="!"
          className="summary-unresolved"
        />
      </div>

      {/* Sections */}
      <div className="results-sections">
        {SECTIONS.map(
          ({ key, title, description, icon, className }) => {
            const items = results[key] || []

            if (items.length === 0) return null

            return (
              <section
                key={key}
                className={`result-section ${className}`}
              >
                <div className="section-heading">
                  <div className="section-heading-left">
                    <div className="section-icon">{icon}</div>

                    <div>
                      <h3>
                        {title}
                        <span className="section-count">
                          {items.length}
                        </span>
                      </h3>

                      <p>{description}</p>
                    </div>
                  </div>
                </div>

                <div className="result-list">
                  {items.map((result, index) => (
                    <ResultCard
                      key={index}
                      result={result}
                      sectionKey={key}
                    />
                  ))}
                </div>
              </section>
            )
          }
        )}
      </div>
    </div>
  )
}

function SummaryCard({
  value,
  label,
  icon,
  className,
}) {
  return (
    <div className={`summary-card ${className}`}>
      <div className="summary-icon">{icon}</div>

      <div className="summary-content">
        <strong>{value}</strong>
        <span>{label}</span>
      </div>
    </div>
  )
}

function ResultCard({ result, sectionKey }) {
  const displayValue = formatValue(result.value)
  const displayUnit = formatValue(result.unit)

  const hasRange =
    Array.isArray(result.normal_range) &&
    result.normal_range.length >= 2

  const rangeText = hasRange
    ? `${formatValue(result.normal_range[0])} – ${formatValue(
        result.normal_range[1]
      )}`
    : null

  const isUnresolved = sectionKey === 'unresolved'

  return (
    <article className="result-card">

      {/* Result top */}
      <div className="result-top">

        <div className="result-title-area">
          <h4>{result.test_name || 'Unknown test'}</h4>

          <div className="result-value">
            <span className="value-number">
              {displayValue}
            </span>

            {displayUnit && (
              <span className="value-unit">
                {displayUnit}
              </span>
            )}
          </div>
        </div>

        <SeverityBadge status={result.status} />
      </div>

      {/* Reference range */}
      {rangeText && (
        <div className="reference-row">
          <span className="reference-label">
            Reference range
          </span>

          <span className="reference-value">
            {rangeText}
            {displayUnit && ` ${displayUnit}`}
          </span>
        </div>
      )}

      {/* Error */}
      {result.error && (
        <div className="data-issue">
          <span className="data-issue-icon">!</span>

          <div>
            <strong>Data issue</strong>
            <p>{formatValue(result.error)}</p>
          </div>
        </div>
      )}

      {/* AI explanation */}
      {result.explanation && (
        <div className="explanation-box">
          <div className="explanation-heading">
            <span className="ai-icon">✦</span>
            <span>AI interpretation</span>
          </div>

          <p>
            {formatValue(result.explanation)}
          </p>
        </div>
      )}

      {/* Next steps */}
      {Array.isArray(result.next_steps) &&
        result.next_steps.length > 0 && (
          <div className="next-steps">
            <div className="next-steps-heading">
              Recommended next steps
            </div>

            <ul>
              {result.next_steps.map((step, index) => (
                <li key={index}>
                  <span className="step-dot">•</span>
                  <span>{formatValue(step)}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

      {/* Unresolved footer */}
      {isUnresolved && !result.explanation && (
        <div className="unresolved-note">
          This result requires manual review.
        </div>
      )}
    </article>
  )
}

/*
 * Presentation-only helper.
 *
 * Normally value/unit/error/explanation are strings or numbers.
 * If an unexpected object reaches the UI, don't render
 * "[object Object]". Display its useful contents instead.
 */
function formatValue(value) {
  if (value === null || value === undefined) {
    return ''
  }

  if (
    typeof value === 'string' ||
    typeof value === 'number' ||
    typeof value === 'boolean'
  ) {
    return String(value)
  }

  if (Array.isArray(value)) {
    return value.map(formatValue).join(' – ')
  }

  if (typeof value === 'object') {
    if ('message' in value) {
      return formatValue(value.message)
    }

    if ('error' in value) {
      return formatValue(value.error)
    }

    if ('reason' in value) {
      return formatValue(value.reason)
    }

    if ('value' in value) {
      return formatValue(value.value)
    }

    try {
      return JSON.stringify(value)
    } catch {
      return 'Unavailable'
    }
  }

  return String(value)
}