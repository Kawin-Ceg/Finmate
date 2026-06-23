import './Features.css';

const FEATURES = [
  {
    eyebrow: 'Auto-tagging',
    title: 'Smart Expense Categorization',
    description:
      'Every transaction is automatically classified into 12+ spending categories using machine learning — no manual tagging required.',
    preview: (
      <div className="feat-preview feat-preview--tags">
        <div className="fpt-row">
          <span className="fpt-merchant">Swiggy</span>
          <span className="fpt-tag fpt-tag--orange">Food &amp; Dining</span>
        </div>
        <div className="fpt-row">
          <span className="fpt-merchant">Ola Cab</span>
          <span className="fpt-tag fpt-tag--blue">Transport</span>
        </div>
        <div className="fpt-row">
          <span className="fpt-merchant">Netflix</span>
          <span className="fpt-tag fpt-tag--purple">Entertainment</span>
        </div>
      </div>
    ),
  },
  {
    eyebrow: 'Analytics',
    title: 'Spending Analytics',
    description:
      'Visual breakdowns by category, merchant, and month. Understand patterns before they become habits.',
    preview: (
      <div className="feat-preview feat-preview--bars">
        {[
          { label: 'Food', pct: 74, color: '#2563EB' },
          { label: 'Shopping', pct: 52, color: '#8B5CF6' },
          { label: 'Transport', pct: 36, color: '#10B981' },
          { label: 'Utilities', pct: 28, color: '#F59E0B' },
        ].map((b) => (
          <div className="fpt-bar-row" key={b.label}>
            <span className="fpt-bar-label">{b.label}</span>
            <div className="fpt-bar-track">
              <div
                className="fpt-bar-fill"
                style={{ width: `${b.pct}%`, background: b.color }}
              />
            </div>
            <span className="fpt-bar-pct">{b.pct}%</span>
          </div>
        ))}
      </div>
    ),
  },
  {
    eyebrow: 'Budgets',
    title: 'Budget Intelligence',
    description:
      'Set monthly limits per category. Get early warnings before you overspend — not a post-mortem.',
    preview: (
      <div className="feat-preview feat-preview--budget">
        <div className="fpt-budget-item">
          <div className="fpt-budget-top">
            <span className="fpt-budget-cat">Food &amp; Dining</span>
            <span className="fpt-budget-amt">₹8,200 / ₹10,000</span>
          </div>
          <div className="fpt-budget-bar">
            <div className="fpt-budget-fill" style={{ width: '82%', background: '#F59E0B' }} />
          </div>
          <span className="fpt-budget-warn">⚠ 82% used · 9 days left</span>
        </div>
        <div className="fpt-budget-item">
          <div className="fpt-budget-top">
            <span className="fpt-budget-cat">Transportation</span>
            <span className="fpt-budget-amt">₹3,100 / ₹5,000</span>
          </div>
          <div className="fpt-budget-bar">
            <div className="fpt-budget-fill" style={{ width: '62%', background: '#10B981' }} />
          </div>
          <span className="fpt-budget-ok">On track</span>
        </div>
      </div>
    ),
  },
  {
    eyebrow: 'ML-powered',
    title: 'Anomaly Detection',
    description:
      'Machine learning identifies unusual spending spikes and outlier transactions you might otherwise miss.',
    preview: (
      <div className="feat-preview feat-preview--anomaly">
        <div className="fpt-alert">
          <div className="fpt-alert-icon">⚡</div>
          <div className="fpt-alert-body">
            <span className="fpt-alert-title">Unusual transaction detected</span>
            <span className="fpt-alert-sub">Amazon · ₹12,500 · 3.4× above average</span>
          </div>
        </div>
        <div className="fpt-alert fpt-alert--muted">
          <div className="fpt-alert-icon fpt-alert-icon--muted">📍</div>
          <div className="fpt-alert-body">
            <span className="fpt-alert-title">New merchant</span>
            <span className="fpt-alert-sub">First transaction from AliExpress</span>
          </div>
        </div>
      </div>
    ),
  },
  {
    eyebrow: 'Health score',
    title: 'Financial Health Score',
    description:
      'A single score that summarizes your financial discipline — updated with every transaction automatically.',
    preview: (
      <div className="feat-preview feat-preview--score">
        <div className="fpt-score-ring">
          <svg viewBox="0 0 80 80" className="fpt-score-svg">
            <circle cx="40" cy="40" r="32" fill="none" stroke="#E2E8F0" strokeWidth="6" />
            <circle
              cx="40" cy="40" r="32"
              fill="none"
              stroke="#2563EB"
              strokeWidth="6"
              strokeDasharray="174 28"
              strokeDashoffset="44"
              strokeLinecap="round"
            />
          </svg>
          <div className="fpt-score-center">
            <span className="fpt-score-num">87</span>
            <span className="fpt-score-lbl">/ 100</span>
          </div>
        </div>
        <span className="fpt-score-badge">Excellent</span>
      </div>
    ),
  },
  {
    eyebrow: 'AI assistant',
    title: 'AI Financial Assistant',
    description:
      'Ask questions about your finances in plain language. Powered by RAG over your personal transaction history.',
    preview: (
      <div className="feat-preview feat-preview--chat">
        <div className="fpt-chat-bubble fpt-chat-bubble--user">
          How much did I spend on food last month?
        </div>
        <div className="fpt-chat-bubble fpt-chat-bubble--ai">
          <span className="fpt-chat-ai-label">AI</span>
          You spent ₹8,200 on food in June — 18% more than May's ₹6,950.
        </div>
      </div>
    ),
  },
];

export default function Features() {
  return (
    <section className="features" id="features">
      <div className="features-inner">
        <div className="features-header">
          <span className="section-eyebrow">Features</span>
          <h2 className="features-title">
            Everything you need to understand your money
          </h2>
          <p className="features-sub">
            Built on top of machine learning and a RAG-powered AI engine,
            FinMate turns raw transactions into actionable intelligence.
          </p>
        </div>

        <div className="features-grid">
          {FEATURES.map((f) => (
            <div className="feat-card" key={f.title}>
              <div className="feat-card-preview">{f.preview}</div>
              <div className="feat-card-body">
                <span className="feat-eyebrow">{f.eyebrow}</span>
                <h3 className="feat-title">{f.title}</h3>
                <p className="feat-desc">{f.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
