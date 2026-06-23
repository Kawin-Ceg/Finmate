import { useState, useEffect, useRef, useCallback } from 'react';
import {
  MessageCircle, Plus, Search, Trash2, Edit3, Check, X,
  BarChart2, Heart, AlertTriangle, TrendingUp, Zap,
  ShoppingCart, RefreshCw, Download, ChevronLeft,
  Send, Bot, User, Loader, PiggyBank, Sparkles,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  sendMessage, getSessions, getSession, createSession,
  renameSession, deleteSession, deleteAllSessions,
  searchChats, getSuggestions, exportChats,
} from '../../services/mateService';
import './MatePage.css';

const ICON_MAP = {
  BarChart2, Heart, AlertTriangle, TrendingUp, Zap,
  ShoppingCart, RefreshCw, PiggyBank,
};

const SERVICE_COLORS = {
  analytics: '#3b82f6',
  health_score: '#10b981',
  budgets: '#f59e0b',
  forecasting: '#8b5cf6',
  anomaly_detection: '#ef4444',
  transactions: '#06b6d4',
};

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

function TypingIndicator() {
  return (
    <div className="mate-msg mate-msg--assistant">
      <div className="mate-msg__avatar"><Bot size={16} /></div>
      <div className="mate-msg__bubble mate-msg__bubble--typing">
        <span /><span /><span />
      </div>
    </div>
  );
}

function SourceBadges({ sources = [], usedServices = [] }) {
  if (!sources?.length && !usedServices?.length) return null;
  return (
    <div className="mate-sources">
      <span className="mate-sources__label">Based on:</span>
      {usedServices?.map(s => (
        <span
          key={s}
          className="mate-sources__badge"
          style={{ borderColor: SERVICE_COLORS[s] || '#64748b', color: SERVICE_COLORS[s] || '#64748b' }}
        >
          {s.replace(/_/g, ' ')}
        </span>
      ))}
    </div>
  );
}

function ChatMessage({ msg }) {
  const isUser = msg.role === 'user';
  return (
    <div className={`mate-msg mate-msg--${isUser ? 'user' : 'assistant'}`}>
      {!isUser && (
        <div className="mate-msg__avatar"><Bot size={16} /></div>
      )}
      <div className={`mate-msg__bubble mate-msg__bubble--${isUser ? 'user' : 'assistant'}`}>
        {isUser ? (
          <p>{msg.content}</p>
        ) : (
          <div className="mate-msg__markdown">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
          </div>
        )}
        {!isUser && (msg.sources?.length > 0 || msg.used_services?.length > 0) && (
          <SourceBadges sources={msg.sources} usedServices={msg.used_services} />
        )}
        <span className="mate-msg__time">
          {new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
      {isUser && (
        <div className="mate-msg__avatar mate-msg__avatar--user"><User size={16} /></div>
      )}
    </div>
  );
}

function QuickActions({ suggestions, onSelect }) {
  return (
    <div className="mate-quick">
      <div className="mate-quick__grid">
        {suggestions.map((s, i) => {
          const Icon = ICON_MAP[s.icon] || MessageCircle;
          return (
            <button key={i} className="mate-quick__card" onClick={() => onSelect(s.text)}>
              <span className="mate-quick__icon"><Icon size={18} /></span>
              <span className="mate-quick__text">{s.text}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

function SessionItem({ session, active, onSelect, onRename, onDelete }) {
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(session.title);
  const inputRef = useRef(null);

  const startEdit = (e) => { e.stopPropagation(); setEditing(true); setTimeout(() => inputRef.current?.focus(), 0); };
  const cancelEdit = (e) => { e.stopPropagation(); setTitle(session.title); setEditing(false); };
  const saveEdit = (e) => {
    e.stopPropagation();
    if (title.trim() && title !== session.title) onRename(session.id, title.trim());
    setEditing(false);
  };

  return (
    <div className={`mate-session-item ${active ? 'mate-session-item--active' : ''}`} onClick={() => onSelect(session.id)}>
      <MessageCircle size={14} className="mate-session-item__icon" />
      <div className="mate-session-item__body">
        {editing ? (
          <input
            ref={inputRef}
            className="mate-session-item__input"
            value={title}
            onChange={e => setTitle(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter') saveEdit(e); if (e.key === 'Escape') cancelEdit(e); }}
            onClick={e => e.stopPropagation()}
          />
        ) : (
          <span className="mate-session-item__title">{session.title}</span>
        )}
        {session.last_message_preview && !editing && (
          <span className="mate-session-item__preview">{session.last_message_preview}</span>
        )}
      </div>
      <div className="mate-session-item__actions" onClick={e => e.stopPropagation()}>
        {editing ? (
          <>
            <button className="mate-session-item__btn" onClick={saveEdit}><Check size={12} /></button>
            <button className="mate-session-item__btn" onClick={cancelEdit}><X size={12} /></button>
          </>
        ) : (
          <>
            <button className="mate-session-item__btn" onClick={startEdit}><Edit3 size={12} /></button>
            <button className="mate-session-item__btn mate-session-item__btn--danger" onClick={e => { e.stopPropagation(); onDelete(session.id); }}><Trash2 size={12} /></button>
          </>
        )}
      </div>
    </div>
  );
}

function EmptyState({ suggestions, onSelect }) {
  return (
    <div className="mate-empty">
      <div className="mate-empty__icon">
        <Sparkles size={32} />
      </div>
      <h2 className="mate-empty__title">Mate</h2>
      <p className="mate-empty__subtitle">Your AI Financial Companion</p>
      <p className="mate-empty__desc">
        Ask questions about your spending, budgets, goals, forecasts and financial health.
      </p>
      {suggestions.length > 0 && <QuickActions suggestions={suggestions} onSelect={onSelect} />}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function MatePage() {
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingSession, setLoadingSession] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [deleteConfirm, setDeleteConfirm] = useState(null); // sessionId | 'all'
  const [exportOpen, setExportOpen] = useState(false);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => { scrollToBottom(); }, [messages, loading]);

  useEffect(() => {
    getSessions().then(setSessions).catch(() => {});
    getSuggestions().then(setSuggestions).catch(() => {});
  }, []);

  const loadSession = useCallback(async (id) => {
    setLoadingSession(true);
    try {
      const data = await getSession(id);
      setActiveSessionId(id);
      setMessages(data.messages || []);
      setSearchResults(null);
    } catch {
      /* ignore */
    } finally {
      setLoadingSession(false);
    }
  }, []);

  const handleNewChat = useCallback(() => {
    setActiveSessionId(null);
    setMessages([]);
    setInput('');
    setSearchResults(null);
    inputRef.current?.focus();
  }, []);

  const handleSend = useCallback(async (text) => {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setInput('');

    const tempUserMsg = { id: Date.now(), role: 'user', content: msg, created_at: new Date().toISOString() };
    setMessages(prev => [...prev, tempUserMsg]);
    setLoading(true);

    try {
      const res = await sendMessage(msg, activeSessionId);
      setActiveSessionId(res.session_id);

      const assistantMsg = {
        id: res.message_id,
        role: 'assistant',
        content: res.answer,
        sources: res.sources,
        used_services: res.used_services,
        confidence: res.confidence,
        intent: res.intent,
        created_at: new Date().toISOString(),
      };
      setMessages(prev => [...prev, assistantMsg]);

      setSessions(prev => {
        const exists = prev.find(s => s.id === res.session_id);
        if (exists) {
          return prev.map(s => s.id === res.session_id
            ? { ...s, title: res.session_title, last_message_at: new Date().toISOString(), last_message_preview: res.answer.slice(0, 100) }
            : s
          ).sort((a, b) => new Date(b.last_message_at) - new Date(a.last_message_at));
        }
        return [{ id: res.session_id, title: res.session_title, last_message_at: new Date().toISOString(), message_count: 2 }, ...prev];
      });
    } catch (err) {
      const errMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: 'Sorry, I ran into an error. Please try again.',
        created_at: new Date().toISOString(),
      };
      setMessages(prev => [...prev, errMsg]);
    } finally {
      setLoading(false);
    }
  }, [input, activeSessionId, loading]);

  const handleRename = useCallback(async (id, title) => {
    await renameSession(id, title);
    setSessions(prev => prev.map(s => s.id === id ? { ...s, title } : s));
  }, []);

  const handleDelete = useCallback(async (id) => {
    await deleteSession(id);
    setSessions(prev => prev.filter(s => s.id !== id));
    if (activeSessionId === id) {
      setActiveSessionId(null);
      setMessages([]);
    }
    setDeleteConfirm(null);
  }, [activeSessionId]);

  const handleDeleteAll = useCallback(async () => {
    await deleteAllSessions();
    setSessions([]);
    setActiveSessionId(null);
    setMessages([]);
    setDeleteConfirm(null);
  }, []);

  const handleSearch = useCallback(async (q) => {
    setSearchQuery(q);
    if (q.trim().length < 2) { setSearchResults(null); return; }
    try {
      const results = await searchChats(q.trim());
      setSearchResults(results);
    } catch { setSearchResults([]); }
  }, []);

  const filteredSessions = searchQuery
    ? sessions.filter(s => s.title.toLowerCase().includes(searchQuery.toLowerCase()))
    : sessions;

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="mate-page">
      {/* Sidebar */}
      <aside className={`mate-sidebar ${sidebarOpen ? 'mate-sidebar--open' : 'mate-sidebar--closed'}`}>
        <div className="mate-sidebar__header">
          <button className="mate-sidebar__new-btn" onClick={handleNewChat}>
            <Plus size={16} /> New Chat
          </button>
          <button className="mate-sidebar__toggle" onClick={() => setSidebarOpen(false)}>
            <ChevronLeft size={16} />
          </button>
        </div>

        <div className="mate-sidebar__search">
          <Search size={14} className="mate-sidebar__search-icon" />
          <input
            className="mate-sidebar__search-input"
            placeholder="Search conversations..."
            value={searchQuery}
            onChange={e => handleSearch(e.target.value)}
          />
        </div>

        <div className="mate-sidebar__sessions">
          {searchResults ? (
            <>
              <p className="mate-sidebar__section-label">{searchResults.length} result{searchResults.length !== 1 ? 's' : ''}</p>
              {searchResults.map(r => (
                <div key={r.message_id} className="mate-search-result" onClick={() => { loadSession(r.session_id); setSearchQuery(''); setSearchResults(null); }}>
                  <span className="mate-search-result__session">{r.session_title}</span>
                  <span className="mate-search-result__preview">{r.content_preview}</span>
                </div>
              ))}
            </>
          ) : (
            <>
              {filteredSessions.length === 0 ? (
                <p className="mate-sidebar__empty">No conversations yet</p>
              ) : (
                <>
                  <p className="mate-sidebar__section-label">Recent</p>
                  {filteredSessions.map(s => (
                    <SessionItem
                      key={s.id}
                      session={s}
                      active={s.id === activeSessionId}
                      onSelect={loadSession}
                      onRename={handleRename}
                      onDelete={(id) => setDeleteConfirm(id)}
                    />
                  ))}
                </>
              )}
            </>
          )}
        </div>

        <div className="mate-sidebar__footer">
          <button className="mate-sidebar__footer-btn" onClick={() => setExportOpen(true)}>
            <Download size={14} /> Export
          </button>
          {sessions.length > 0 && (
            <button className="mate-sidebar__footer-btn mate-sidebar__footer-btn--danger" onClick={() => setDeleteConfirm('all')}>
              <Trash2 size={14} /> Clear All
            </button>
          )}
        </div>
      </aside>

      {/* Main chat area */}
      <div className="mate-main">
        {/* Topbar */}
        <div className="mate-topbar">
          {!sidebarOpen && (
            <button className="mate-topbar__toggle" onClick={() => setSidebarOpen(true)}>
              <MessageCircle size={18} />
            </button>
          )}
          <div className="mate-topbar__title">
            <Sparkles size={18} className="mate-topbar__sparkle" />
            <span>Mate</span>
            <span className="mate-topbar__subtitle">AI Financial Companion</span>
          </div>
          {activeSessionId && (
            <div className="mate-topbar__actions">
              <button className="mate-topbar__btn" onClick={() => exportChats('markdown', activeSessionId)} title="Export chat">
                <Download size={16} />
              </button>
              <button className="mate-topbar__btn mate-topbar__btn--danger" onClick={() => setDeleteConfirm(activeSessionId)} title="Delete chat">
                <Trash2 size={16} />
              </button>
            </div>
          )}
        </div>

        {/* Messages */}
        <div className="mate-messages">
          {loadingSession ? (
            <div className="mate-loading-session">
              <Loader size={24} className="mate-spin" />
            </div>
          ) : messages.length === 0 ? (
            <EmptyState suggestions={suggestions} onSelect={handleSend} />
          ) : (
            <>
              {messages.map(msg => <ChatMessage key={msg.id} msg={msg} />)}
              {loading && <TypingIndicator />}
              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input */}
        <div className="mate-input-wrap">
          <div className="mate-input-box">
            <textarea
              ref={inputRef}
              className="mate-input"
              placeholder="Ask about your finances..."
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              rows={1}
            />
            <button
              className={`mate-send-btn ${loading || !input.trim() ? 'mate-send-btn--disabled' : ''}`}
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
            >
              {loading ? <Loader size={18} className="mate-spin" /> : <Send size={18} />}
            </button>
          </div>
          <p className="mate-input-hint">
            Mate provides financial insights for informational purposes only. Not financial advice.
          </p>
        </div>
      </div>

      {/* Delete confirmation modal */}
      {deleteConfirm && (
        <div className="mate-modal-overlay" onClick={() => setDeleteConfirm(null)}>
          <div className="mate-modal" onClick={e => e.stopPropagation()}>
            <h3>{deleteConfirm === 'all' ? 'Delete all conversations?' : 'Delete this conversation?'}</h3>
            <p>{deleteConfirm === 'all' ? 'This will permanently delete all your Mate conversations.' : 'This conversation cannot be recovered.'}</p>
            <div className="mate-modal__actions">
              <button className="mate-modal__cancel" onClick={() => setDeleteConfirm(null)}>Cancel</button>
              <button
                className="mate-modal__confirm"
                onClick={() => deleteConfirm === 'all' ? handleDeleteAll() : handleDelete(deleteConfirm)}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Export modal */}
      {exportOpen && (
        <div className="mate-modal-overlay" onClick={() => setExportOpen(false)}>
          <div className="mate-modal" onClick={e => e.stopPropagation()}>
            <h3>Export Conversations</h3>
            <p>Download all your Mate conversations.</p>
            <div className="mate-modal__actions mate-modal__actions--col">
              <button className="mate-modal__option" onClick={() => { exportChats('markdown'); setExportOpen(false); }}>
                <Download size={16} /> Markdown (.md)
              </button>
              <button className="mate-modal__option" onClick={() => { exportChats('json'); setExportOpen(false); }}>
                <Download size={16} /> JSON (.json)
              </button>
            </div>
            <button className="mate-modal__cancel" style={{ marginTop: '8px' }} onClick={() => setExportOpen(false)}>Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}
