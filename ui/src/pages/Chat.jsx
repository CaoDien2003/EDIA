import { useState, useRef, useEffect, useCallback } from 'react'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function Message({ role, content, sources }) {
  const [showSources, setShowSources] = useState(false)
  const isUser = role === 'user'

  return (
    <div style={{
      display: 'flex',
      justifyContent: isUser ? 'flex-end' : 'flex-start',
      marginBottom: '1.25rem',
      gap: '0.75rem',
      alignItems: 'flex-start',
    }}>
      {!isUser && (
        <div style={{
          width: 32, height: 32, borderRadius: '50%',
          background: '#1e293b', color: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 13, fontWeight: 700, flexShrink: 0, marginTop: 2,
        }}>
          AI
        </div>
      )}

      <div style={{ maxWidth: '72%' }}>
        <div style={{
          padding: '0.75rem 1rem',
          borderRadius: isUser ? '1.25rem 1.25rem 0.25rem 1.25rem' : '1.25rem 1.25rem 1.25rem 0.25rem',
          background: isUser ? '#2563eb' : '#f1f5f9',
          color: isUser ? '#fff' : '#1e293b',
          fontSize: '0.95rem',
          lineHeight: '1.65',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}>
          {content}
        </div>

        {sources && sources.length > 0 && (
          <div style={{ marginTop: '0.4rem', paddingLeft: '0.25rem' }}>
            <button
              onClick={() => setShowSources(s => !s)}
              style={{
                background: 'none', border: 'none', padding: 0,
                color: '#64748b', fontSize: '0.8rem', cursor: 'pointer',
                textDecoration: 'underline', textUnderlineOffset: '2px',
              }}
            >
              {showSources ? 'Hide sources' : `${sources.length} source${sources.length > 1 ? 's' : ''}`}
            </button>
            {showSources && (
              <ul style={{ marginTop: '0.4rem', paddingLeft: '1rem', fontSize: '0.82rem', color: '#64748b' }}>
                {sources.map((s, i) => (
                  <li key={i} style={{ marginBottom: '0.15rem' }}>
                    <strong>{s.file}</strong> — page {s.page + 1}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </div>

      {isUser && (
        <div style={{
          width: 32, height: 32, borderRadius: '50%',
          background: '#2563eb', color: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 13, fontWeight: 700, flexShrink: 0, marginTop: 2,
        }}>
          You
        </div>
      )}
    </div>
  )
}

function TypingIndicator() {
  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem', marginBottom: '1.25rem' }}>
      <div style={{
        width: 32, height: 32, borderRadius: '50%',
        background: '#1e293b', color: '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: 13, fontWeight: 700, flexShrink: 0,
      }}>
        AI
      </div>
      <div style={{
        padding: '0.75rem 1rem',
        borderRadius: '1.25rem 1.25rem 1.25rem 0.25rem',
        background: '#f1f5f9',
        display: 'flex', gap: '4px', alignItems: 'center',
      }}>
        {[0, 1, 2].map(i => (
          <span key={i} style={{
            width: 7, height: 7, borderRadius: '50%',
            background: '#94a3b8',
            animation: 'bounce 1.2s ease-in-out infinite',
            animationDelay: `${i * 0.2}s`,
            display: 'block',
          }} />
        ))}
      </div>
      <style>{`
        @keyframes bounce {
          0%, 80%, 100% { transform: translateY(0); }
          40% { transform: translateY(-6px); }
        }
      `}</style>
    </div>
  )
}

export default function Chat() {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // auto-resize textarea
  useEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = Math.min(el.scrollHeight, 160) + 'px'
  }, [input])

  const send = useCallback(async () => {
    const question = input.trim()
    if (!question || loading) return

    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: question }])
    setLoading(true)

    try {
      const resp = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question }),
      })
      const data = await resp.json()
      if (!resp.ok) throw new Error(data.detail || 'Request failed')

      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.answer,
        sources: data.sources,
      }])
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `Error: ${err.message}`,
      }])
    } finally {
      setLoading(false)
    }
  }, [input, loading])

  function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      send()
    }
  }

  const canSend = input.trim() && !loading

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0.875rem 1.5rem',
        borderBottom: '1px solid #e2e8f0',
        background: '#fff',
        position: 'sticky', top: 0, zIndex: 10,
      }}>
        <div style={{ fontWeight: 700, fontSize: '1rem', color: '#1e293b' }}>
          PDF AI Assistant
        </div>
        {messages.length > 0 && (
          <button
            onClick={() => setMessages([])}
            style={{
              background: 'none', border: '1px solid #e2e8f0',
              borderRadius: '0.5rem', padding: '0.3rem 0.75rem',
              color: '#64748b', fontSize: '0.82rem', cursor: 'pointer',
            }}
          >
            New chat
          </button>
        )}
      </div>

      {/* Messages */}
      <div style={{
        flex: 1, overflowY: 'auto',
        padding: '2rem 1rem',
      }}>
        <div style={{ maxWidth: 720, margin: '0 auto' }}>
          {messages.length === 0 && (
            <div style={{
              textAlign: 'center', color: '#94a3b8',
              marginTop: '30vh', fontSize: '1.05rem',
            }}>
              Ask anything about your uploaded documents
            </div>
          )}

          {messages.map((msg, i) => (
            <Message key={i} {...msg} />
          ))}

          {loading && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input */}
      <div style={{
        padding: '1rem 1rem 1.25rem',
        borderTop: '1px solid #e2e8f0',
        background: '#fff',
      }}>
        <div style={{
          maxWidth: 720, margin: '0 auto',
          display: 'flex', gap: '0.625rem', alignItems: 'flex-end',
          border: '1px solid #e2e8f0', borderRadius: '0.875rem',
          padding: '0.5rem 0.5rem 0.5rem 1rem',
          boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
          background: '#fff',
        }}>
          <textarea
            ref={textareaRef}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question... (Enter to send, Shift+Enter for new line)"
            rows={1}
            style={{
              flex: 1, resize: 'none', border: 'none', outline: 'none',
              fontSize: '0.95rem', fontFamily: 'inherit',
              lineHeight: '1.6', background: 'transparent',
              maxHeight: 160, overflowY: 'auto',
              padding: '0.25rem 0',
            }}
          />
          <button
            onClick={send}
            disabled={!canSend}
            style={{
              width: 36, height: 36, borderRadius: '0.625rem',
              background: canSend ? '#2563eb' : '#e2e8f0',
              border: 'none', cursor: canSend ? 'pointer' : 'not-allowed',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              flexShrink: 0, transition: 'background 0.15s',
            }}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={canSend ? '#fff' : '#94a3b8'} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13" />
              <polygon points="22 2 15 22 11 13 2 9 22 2" />
            </svg>
          </button>
        </div>
        <p style={{ textAlign: 'center', fontSize: '0.75rem', color: '#cbd5e1', marginTop: '0.5rem' }}>
          Answers are based only on uploaded documents
        </p>
      </div>
    </div>
  )
}
