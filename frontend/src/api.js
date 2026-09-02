const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

export async function analyzeLabs(labs, patientId) {
  const res = await fetch(`${BASE_URL}/analyze_labs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ patient_id: patientId || null, labs }),
  })

  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed (${res.status})`)
  }

  return res.json()
}
