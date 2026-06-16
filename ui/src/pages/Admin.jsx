import { useState, useRef, useEffect } from 'react'

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// ── Shared styles ────────────────────────────────────────────────
const s = {
  card: {
    background: '#fff',
    border: '1px solid #e2e8f0',
    borderRadius: '0.75rem',
    padding: '1.5rem',
    marginBottom: '1.25rem',
  },
  input: {
    width: '100%',
    padding: '0.625rem 0.875rem',
    border: '1px solid #e2e8f0',
    borderRadius: '0.5rem',
    fontSize: '0.95rem',
    outline: 'none',
    fontFamily: 'inherit',
    color: '#1e293b',
    background: '#fff',
    boxSizing: 'border-box',
  },
  btn: (variant = 'primary') => ({
    padding: '0.5rem 1rem',
    background: variant === 'primary' ? '#1e293b' : variant === 'danger' ? 'none' : '#fff',
    color: variant === 'primary' ? '#fff' : variant === 'danger' ? '#dc2626' : '#64748b',
    border: variant === 'primary' ? 'none' : `1px solid ${variant === 'danger' ? '#fecaca' : '#e2e8f0'}`,
    borderRadius: '0.5rem',
    fontWeight: 600,
    fontSize: '0.85rem',
    cursor: 'pointer',
    fontFamily: 'inherit',
    transition: 'opacity 0.15s',
    whiteSpace: 'nowrap',
  }),
  label: {
    fontSize: '0.75rem',
    fontWeight: 600,
    color: '#64748b',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
}

// ── Toast ────────────────────────────────────────────────────────
function Toast({ msg, onClose }) {
  if (!msg) return null
  const isErr = msg.type === 'error'
  return (
    <div style={{
      padding: '0.75rem 1rem',
      borderRadius: '0.5rem',
      marginBottom: '1.25rem',
      background: isErr ? '#fef2f2' : '#f0fdf4',
      color: isErr ? '#dc2626' : '#15803d',
      border: `1px solid ${isErr ? '#fecaca' : '#bbf7d0'}`,
      fontSize: '0.875rem',
      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    }}>
      {msg.text}
      <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', fontSize: '1rem' }}>×</button>
    </div>
  )
}

// ── Login ────────────────────────────────────────────────────────
function LoginScreen({ onLogin }) {
  const [key, setKey] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const resp = await fetch(`${API}/api/v1/documents`, {
        headers: { 'X-Admin-Key': key },
      })
      if (resp.ok) {
        onLogin(key, await resp.json())
      } else {
        setError('Invalid admin key.')
      }
    } catch {
      setError('Cannot connect to API.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#f8fafc' }}>
      <div style={{ ...s.card, width: 360 }}>
        <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '0.25rem', color: '#1e293b' }}>Admin</h2>
        <p style={{ fontSize: '0.85rem', color: '#94a3b8', marginBottom: '1.25rem' }}>Document Intelligence Assistant</p>
        <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <input
            type="password" value={key}
            onChange={e => setKey(e.target.value)}
            placeholder="Admin key" autoFocus style={s.input}
          />
          {error && <p style={{ color: '#dc2626', fontSize: '0.85rem', margin: 0 }}>{error}</p>}
          <button type="submit" disabled={loading || !key}
            style={{ ...s.btn('primary'), opacity: loading || !key ? 0.5 : 1 }}>
            {loading ? 'Checking…' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  )
}

// ── Stat card ────────────────────────────────────────────────────
function Stat({ label, value, unit }) {
  return (
    <div style={{
      background: '#f8fafc', border: '1px solid #e2e8f0',
      borderRadius: '0.625rem', padding: '1rem 1.25rem', flex: 1, minWidth: 120,
    }}>
      <div style={{ fontSize: '0.72rem', fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.4rem' }}>
        {label}
      </div>
      <div style={{ fontSize: '1.6rem', fontWeight: 700, color: '#1e293b', lineHeight: 1 }}>
        {value ?? '—'}
        {unit && <span style={{ fontSize: '0.85rem', fontWeight: 500, color: '#64748b', marginLeft: 4 }}>{unit}</span>}
      </div>
    </div>
  )
}

// ── Extraction result ────────────────────────────────────────────
function ExtractionPanel({ docId, adminKey, onClose }) {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetch(`${API}/api/v1/documents/${docId}/extract`, {
      method: 'POST',
      headers: { 'X-Admin-Key': adminKey },
    })
      .then(r => r.json())
      .then(data => { setResult(data.fields); setLoading(false) })
      .catch(e => { setError(e.message); setLoading(false) })
  }, [docId, adminKey])

  const riskColor = { high: '#dc2626', medium: '#d97706', low: '#15803d' }

  return (
    <tr>
      <td colSpan={5} style={{ padding: 0 }}>
        <div style={{
          background: '#f8fafc', border: '1px solid #e2e8f0',
          borderRadius: '0.5rem', margin: '0.25rem 0 0.75rem',
          padding: '1rem 1.25rem',
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
            <span style={{ fontWeight: 600, fontSize: '0.875rem', color: '#1e293b' }}>Structured Extraction</span>
            <button onClick={onClose} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer', fontSize: '1rem' }}>×</button>
          </div>

          {loading && <p style={{ color: '#94a3b8', fontSize: '0.875rem' }}>Extracting with AI…</p>}
          {error && <p style={{ color: '#dc2626', fontSize: '0.875rem' }}>Error: {error}</p>}
          {result && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', fontSize: '0.85rem' }}>
              {result.risk_level && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={s.label}>Risk</span>
                  <span style={{
                    padding: '0.2rem 0.6rem', borderRadius: '999px', fontWeight: 600,
                    background: riskColor[result.risk_level] + '18',
                    color: riskColor[result.risk_level] || '#64748b',
                    fontSize: '0.8rem',
                  }}>
                    {result.risk_level?.toUpperCase()}
                  </span>
                </div>
              )}
              {result.parties?.length > 0 && (
                <div><span style={s.label}>Parties: </span>{result.parties.join(', ')}</div>
              )}
              {result.effective_date && (
                <div><span style={s.label}>Effective date: </span>{result.effective_date}</div>
              )}
              {result.value && (
                <div><span style={s.label}>Value: </span>{result.currency} {result.value?.toLocaleString()}</div>
              )}
              {result.risks?.length > 0 && (
                <div>
                  <div style={s.label}>Risks:</div>
                  <ul style={{ margin: '0.25rem 0 0 1rem', padding: 0, color: '#dc2626' }}>
                    {result.risks.map((r, i) => <li key={i} style={{ marginBottom: '0.2rem' }}>{r}</li>)}
                  </ul>
                </div>
              )}
              {result.penalty_clauses?.length > 0 && (
                <div>
                  <div style={s.label}>Penalty clauses:</div>
                  <ul style={{ margin: '0.25rem 0 0 1rem', padding: 0 }}>
                    {result.penalty_clauses.map((p, i) => <li key={i} style={{ marginBottom: '0.2rem' }}>{p}</li>)}
                  </ul>
                </div>
              )}
              <details style={{ marginTop: '0.5rem' }}>
                <summary style={{ cursor: 'pointer', color: '#64748b', fontSize: '0.8rem' }}>Raw JSON</summary>
                <pre style={{
                  marginTop: '0.5rem', background: '#1e293b', color: '#e2e8f0',
                  padding: '0.75rem', borderRadius: '0.375rem',
                  fontSize: '0.78rem', overflowX: 'auto',
                }}>
                  {JSON.stringify(result, null, 2)}
                </pre>
              </details>
            </div>
          )}
        </div>
      </td>
    </tr>
  )
}

// ── Main Admin ───────────────────────────────────────────────────
export default function Admin() {
  const [adminKey, setAdminKey] = useState(null)
  const [docs, setDocs] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [uploading, setUploading] = useState(false)
  const [toast, setToast] = useState(null)
  const [extractingId, setExtractingId] = useState(null)
  const fileRef = useRef(null)

  function showToast(type, text) { setToast({ type, text }) }

  async function fetchDocs(key = adminKey) {
    const resp = await fetch(`${API}/api/v1/documents`, { headers: { 'X-Admin-Key': key } })
    if (resp.ok) setDocs(await resp.json())
  }

  async function fetchAnalytics(key = adminKey) {
    try {
      const resp = await fetch(`${API}/api/v1/analytics/summary`, { headers: { 'X-Admin-Key': key } })
      if (resp.ok) setAnalytics(await resp.json())
    } catch { /* non-critical */ }
  }

  async function onLogin(key, initialDocs) {
    setAdminKey(key)
    setDocs(initialDocs)
    fetchAnalytics(key)
  }

  async function upload() {
    const file = fileRef.current?.files[0]
    if (!file) return
    setUploading(true)
    setToast(null)
    const form = new FormData()
    form.append('file', file)
    try {
      const resp = await fetch(`${API}/api/v1/documents/upload`, {
        method: 'POST',
        headers: { 'X-Admin-Key': adminKey },
        body: form,
      })
      const data = await resp.json()
      if (resp.ok) {
        showToast('success', `Indexed ${data.chunk_count} chunks from ${data.name}`)
        fileRef.current.value = ''
        await Promise.all([fetchDocs(), fetchAnalytics()])
      } else {
        showToast('error', data.detail || 'Upload failed')
      }
    } catch {
      showToast('error', 'Upload failed.')
    } finally {
      setUploading(false)
    }
  }

  async function deleteDoc(doc) {
    if (!confirm(`Delete "${doc.name}"?`)) return
    const resp = await fetch(`${API}/api/v1/documents/${doc.id}`, {
      method: 'DELETE',
      headers: { 'X-Admin-Key': adminKey },
    })
    if (resp.ok) {
      showToast('success', `Deleted ${doc.name}`)
      setDocs(prev => prev.filter(d => d.id !== doc.id))
    } else {
      const data = await resp.json()
      showToast('error', data.detail || 'Delete failed')
    }
  }

  function formatBytes(n) {
    if (!n) return '—'
    if (n < 1024) return `${n} B`
    if (n < 1024 * 1024) return `${(n / 1024).toFixed(0)} KB`
    return `${(n / 1024 / 1024).toFixed(1)} MB`
  }

  function formatDate(iso) {
    return new Date(iso).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
  }

  if (!adminKey) {
    return <LoginScreen onLogin={onLogin} />
  }

  return (
    <div style={{ maxWidth: 800, margin: '0 auto', padding: '2rem 1rem', background: '#f8fafc', minHeight: '100vh' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.75rem' }}>
        <div>
          <h1 style={{ fontSize: '1.35rem', fontWeight: 700, color: '#1e293b', margin: 0 }}>Admin</h1>
          <p style={{ fontSize: '0.82rem', color: '#94a3b8', margin: '0.2rem 0 0' }}>Document Intelligence Assistant</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <a href="/" style={{ ...s.btn('secondary'), textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}>
            Chat
          </a>
          <button onClick={() => { setAdminKey(null); setDocs([]); setAnalytics(null) }} style={s.btn('secondary')}>
            Logout
          </button>
        </div>
      </div>

      <Toast msg={toast} onClose={() => setToast(null)} />

      {/* Analytics */}
      {analytics && (
        <div style={s.card}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#1e293b', margin: 0 }}>
              Analytics
              <span style={{ marginLeft: '0.5rem', fontWeight: 400, color: '#94a3b8', fontSize: '0.82rem' }}>
                last 7 days
              </span>
            </h2>
            <button
              onClick={() => fetchAnalytics()}
              style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: '0.82rem' }}
            >
              Refresh
            </button>
          </div>
          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
            <Stat label="Queries" value={analytics.total_queries} />
            <Stat label="Avg response" value={analytics.avg_response_ms} unit="ms" />
            <Stat label="Uploads" value={analytics.total_uploads} />
            <Stat label="Total docs" value={analytics.total_documents} />
          </div>
        </div>
      )}

      {/* Upload */}
      <div style={s.card}>
        <h2 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#1e293b', marginBottom: '1rem' }}>
          Upload Document
        </h2>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <input ref={fileRef} type="file" accept=".pdf" style={{ flex: 1, minWidth: 0, fontSize: '0.875rem' }} />
          <button onClick={upload} disabled={uploading} style={{ ...s.btn('primary'), opacity: uploading ? 0.6 : 1 }}>
            {uploading ? 'Indexing…' : 'Upload & Index'}
          </button>
        </div>
        {uploading && (
          <p style={{ fontSize: '0.82rem', color: '#64748b', marginTop: '0.75rem', margin: '0.75rem 0 0' }}>
            Chunking and embedding… this may take a moment.
          </p>
        )}
      </div>

      {/* Document list */}
      <div style={s.card}>
        <h2 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#1e293b', marginBottom: '1rem' }}>
          Indexed Documents
          <span style={{ marginLeft: '0.5rem', fontWeight: 400, color: '#94a3b8', fontSize: '0.875rem' }}>
            ({docs.length})
          </span>
        </h2>

        {docs.length === 0 ? (
          <p style={{ color: '#94a3b8', fontSize: '0.9rem' }}>No documents indexed yet.</p>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid #e2e8f0' }}>
                {['File', 'Size', 'Chunks', 'Uploaded', ''].map((h, i) => (
                  <th key={i} style={{
                    textAlign: i === 4 ? 'right' : 'left',
                    padding: '0.5rem 0.5rem 0.75rem',
                    color: '#64748b', fontWeight: 500,
                  }}>
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {docs.map(doc => (
                <>
                  <tr key={doc.id} style={{ borderBottom: '1px solid #f1f5f9' }}>
                    <td style={{ padding: '0.75rem 0.5rem', color: '#1e293b', fontWeight: 500, wordBreak: 'break-all' }}>
                      {doc.name}
                    </td>
                    <td style={{ padding: '0.75rem 0.5rem', color: '#64748b', whiteSpace: 'nowrap' }}>
                      {formatBytes(doc.size_bytes)}
                    </td>
                    <td style={{ padding: '0.75rem 0.5rem', color: '#64748b' }}>
                      {doc.chunk_count}
                    </td>
                    <td style={{ padding: '0.75rem 0.5rem', color: '#64748b', whiteSpace: 'nowrap' }}>
                      {formatDate(doc.uploaded_at)}
                    </td>
                    <td style={{ padding: '0.75rem 0 0.75rem 0.5rem', textAlign: 'right', whiteSpace: 'nowrap' }}>
                      <button
                        onClick={() => setExtractingId(extractingId === doc.id ? null : doc.id)}
                        style={{
                          ...s.btn('secondary'),
                          marginRight: '0.375rem',
                          background: extractingId === doc.id ? '#eff6ff' : undefined,
                          color: extractingId === doc.id ? '#2563eb' : undefined,
                          border: extractingId === doc.id ? '1px solid #bfdbfe' : undefined,
                        }}
                      >
                        Extract
                      </button>
                      <button onClick={() => deleteDoc(doc)} style={s.btn('danger')}>
                        Delete
                      </button>
                    </td>
                  </tr>
                  {extractingId === doc.id && (
                    <ExtractionPanel
                      key={`extract-${doc.id}`}
                      docId={doc.id}
                      adminKey={adminKey}
                      onClose={() => setExtractingId(null)}
                    />
                  )}
                </>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Webhook hint */}
      <div style={{ ...s.card, background: '#fffbeb', border: '1px solid #fde68a' }}>
        <h2 style={{ fontSize: '0.875rem', fontWeight: 600, color: '#92400e', marginBottom: '0.5rem' }}>
          n8n Automation
        </h2>
        <p style={{ fontSize: '0.82rem', color: '#78350f', margin: 0 }}>
          Register webhooks via <code style={{ background: '#fef3c7', padding: '0 4px', borderRadius: 3 }}>POST /api/v1/webhooks</code> to trigger n8n workflows on{' '}
          <strong>document.uploaded</strong>, <strong>document.high_risk</strong>, and <strong>chat.completed</strong> events.
          Import templates from <code style={{ background: '#fef3c7', padding: '0 4px', borderRadius: 3 }}>n8n/workflows/</code>.
        </p>
      </div>
    </div>
  )
}
