import { useState, useRef } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

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
  },
  btn: (primary) => ({
    padding: '0.575rem 1.125rem',
    background: primary ? '#1e293b' : '#fff',
    color: primary ? '#fff' : '#64748b',
    border: primary ? 'none' : '1px solid #e2e8f0',
    borderRadius: '0.5rem',
    fontWeight: 600,
    fontSize: '0.875rem',
    cursor: 'pointer',
    fontFamily: 'inherit',
    transition: 'opacity 0.15s',
  }),
}

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
      <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', fontSize: '1rem', lineHeight: 1 }}>x</button>
    </div>
  )
}

function LoginScreen({ onLogin }) {
  const [key, setKey] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const resp = await fetch(`${API_URL}/admin/documents`, {
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
    <div style={{
      display: 'flex', justifyContent: 'center', alignItems: 'center',
      height: '100vh', background: '#f8fafc',
    }}>
      <div style={{ ...s.card, width: 360 }}>
        <h2 style={{ fontSize: '1.2rem', fontWeight: 700, marginBottom: '1.25rem', color: '#1e293b' }}>
          Admin
        </h2>
        <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <input
            type="password"
            value={key}
            onChange={e => setKey(e.target.value)}
            placeholder="Admin key"
            autoFocus
            style={s.input}
          />
          {error && <p style={{ color: '#dc2626', fontSize: '0.85rem' }}>{error}</p>}
          <button type="submit" disabled={loading || !key} style={{ ...s.btn(true), opacity: loading || !key ? 0.5 : 1 }}>
            {loading ? 'Checking...' : 'Login'}
          </button>
        </form>
      </div>
    </div>
  )
}

export default function Admin() {
  const [adminKey, setAdminKey] = useState(null)
  const [docs, setDocs] = useState([])
  const [uploading, setUploading] = useState(false)
  const [toast, setToast] = useState(null)
  const fileRef = useRef(null)

  function showToast(type, text) {
    setToast({ type, text })
  }

  async function fetchDocs(key = adminKey) {
    const resp = await fetch(`${API_URL}/admin/documents`, {
      headers: { 'X-Admin-Key': key },
    })
    if (resp.ok) setDocs(await resp.json())
  }

  async function upload() {
    const file = fileRef.current?.files[0]
    if (!file) return
    setUploading(true)
    setToast(null)
    const form = new FormData()
    form.append('file', file)
    try {
      const resp = await fetch(`${API_URL}/admin/upload`, {
        method: 'POST',
        headers: { 'X-Admin-Key': adminKey },
        body: form,
      })
      const data = await resp.json()
      if (resp.ok) {
        showToast('success', data.message)
        fileRef.current.value = ''
        await fetchDocs()
      } else {
        showToast('error', data.detail || 'Upload failed')
      }
    } catch {
      showToast('error', 'Upload failed.')
    } finally {
      setUploading(false)
    }
  }

  async function deleteDoc(name) {
    if (!confirm(`Delete "${name}"?`)) return
    const resp = await fetch(`${API_URL}/admin/documents/${encodeURIComponent(name)}`, {
      method: 'DELETE',
      headers: { 'X-Admin-Key': adminKey },
    })
    if (resp.ok) {
      showToast('success', `Deleted ${name}`)
      setDocs(prev => prev.filter(d => d.name !== name))
    } else {
      const data = await resp.json()
      showToast('error', data.detail || 'Delete failed')
    }
  }

  if (!adminKey) {
    return <LoginScreen onLogin={(key, initialDocs) => { setAdminKey(key); setDocs(initialDocs) }} />
  }

  return (
    <div style={{ maxWidth: 700, margin: '0 auto', padding: '2rem 1rem', background: '#f8fafc', minHeight: '100vh' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.75rem' }}>
        <h1 style={{ fontSize: '1.35rem', fontWeight: 700, color: '#1e293b' }}>Admin</h1>
        <button onClick={() => { setAdminKey(null); setDocs([]) }} style={s.btn(false)}>
          Logout
        </button>
      </div>

      <Toast msg={toast} onClose={() => setToast(null)} />

      {/* Upload */}
      <div style={s.card}>
        <h2 style={{ fontSize: '0.95rem', fontWeight: 600, color: '#1e293b', marginBottom: '1rem' }}>
          Upload Document
        </h2>
        <div style={{ display: 'flex', gap: '0.75rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <input ref={fileRef} type="file" accept=".pdf" style={{ flex: 1, minWidth: 0, fontSize: '0.875rem' }} />
          <button onClick={upload} disabled={uploading} style={{ ...s.btn(true), opacity: uploading ? 0.6 : 1, whiteSpace: 'nowrap' }}>
            {uploading ? 'Indexing...' : 'Upload & Index'}
          </button>
        </div>
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
                <th style={{ textAlign: 'left', padding: '0.5rem 0.5rem 0.75rem 0', color: '#64748b', fontWeight: 500 }}>File</th>
                <th style={{ textAlign: 'left', padding: '0.5rem 0.5rem 0.75rem', color: '#64748b', fontWeight: 500 }}>Uploaded</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {docs.map(doc => (
                <tr key={doc.name} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '0.75rem 0.5rem 0.75rem 0', color: '#1e293b', fontWeight: 500 }}>{doc.name}</td>
                  <td style={{ padding: '0.75rem 0.5rem', color: '#64748b' }}>{doc.uploaded_at}</td>
                  <td style={{ padding: '0.75rem 0', textAlign: 'right' }}>
                    <button
                      onClick={() => deleteDoc(doc.name)}
                      style={{
                        background: 'none', border: '1px solid #fecaca',
                        borderRadius: '0.375rem', padding: '0.25rem 0.625rem',
                        color: '#dc2626', cursor: 'pointer', fontSize: '0.8rem',
                        fontFamily: 'inherit',
                      }}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
