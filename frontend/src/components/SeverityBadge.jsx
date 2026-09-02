const CONFIG = {
  Critical: {
    label: 'Critical',
    icon: '🚨',
    color: 'var(--critical)',
    bg: 'var(--critical-bg)',
    border: 'var(--critical-border)',
  },

  Warning: {
    label: 'Warning',
    icon: '⚠',
    color: 'var(--warning)',
    bg: 'var(--warning-bg)',
    border: 'var(--warning-border)',
  },

  Normal: {
    label: 'Normal',
    icon: '✓',
    color: 'var(--normal)',
    bg: 'var(--normal-bg)',
    border: 'var(--normal-border)',
  },

  Unknown: {
    label: 'Unresolved',
    icon: '?',
    color: 'var(--unresolved)',
    bg: 'var(--unresolved-bg)',
    border: 'var(--unresolved-border)',
  },

  Error: {
    label: 'Data issue',
    icon: '!',
    color: 'var(--unresolved)',
    bg: 'var(--unresolved-bg)',
    border: 'var(--unresolved-border)',
  },
}

export default function SeverityBadge({ status }) {
  const cfg = CONFIG[status] || CONFIG.Unknown

  return (
    <span
      className="severity-badge"
      style={{
        color: cfg.color,
        background: cfg.bg,
        borderColor: cfg.border,
      }}
    >
      <span className="severity-badge-icon">{cfg.icon}</span>
      {cfg.label}
    </span>
  )
}