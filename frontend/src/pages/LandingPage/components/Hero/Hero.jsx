import './Hero.css';

const TRANSACTIONS = [
  { merchant: 'Swiggy', category: 'Food', amount: '-₹680', positive: false },
  { merchant: 'ACME Corp — Salary', category: 'Income', amount: '+₹85,000', positive: true },
  { merchant: 'Netflix', category: 'Entertainment', amount: '-₹649', positive: false },
  { merchant: 'PharmEasy', category: 'Health', amount: '-₹1,230', positive: false },
];

export default function Hero() {
  return (
    <section className="hero">
      <div className="hero-bg-grid" aria-hidden="true" />

      <div className="hero-inner">
        <div className="hero-text">
          <a href="/signup" className="hero-announce">
            <span className="hero-announce-dot" />
            <span>Now in public beta</span>
            <span className="hero-announce-arrow">→</span>
          </a>

          <h1 className="hero-headline">
            Stop tracking expenses.<br />
            <span className="hero-headline-accent">Start understanding them.</span>
          </h1>

          <p className="hero-sub">
            FinMate uses AI to analyze your spending patterns, auto-categorize
            every transaction, detect unusual activity, and deliver insights
            that actually change your financial habits.
          </p>

          <div className="hero-actions">
            <a href="/signup" className="hero-btn-primary">
              Get started free
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M3 7H11M11 7L7.5 3.5M11 7L7.5 10.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </a>
            <a href="#how-it-works" className="hero-btn-secondary">
              See how it works
            </a>
          </div>

          <p className="hero-trust">
            No credit card required
            <span className="hero-trust-dot" />
            No bank connection needed
            <span className="hero-trust-dot" />
            Built for India
          </p>
        </div>

        <div className="hero-visual" aria-hidden="true">
          <div className="hero-mockup">
            <div className="mockup-window-bar">
              <div className="mockup-dots">
                <span className="mockup-dot mockup-dot--red" />
                <span className="mockup-dot mockup-dot--yellow" />
                <span className="mockup-dot mockup-dot--green" />
              </div>
              <span className="mockup-url">finmate.app/dashboard</span>
            </div>

            <div className="mockup-body">
              <div className="mockup-stats-row">
                <div className="mockup-stat">
                  <span className="mockup-stat-value">₹47,280</span>
                  <span className="mockup-stat-label">Monthly spending</span>
                </div>
                <div className="mockup-stat-divider" />
                <div className="mockup-stat">
                  <span className="mockup-stat-value">₹12,450</span>
                  <span className="mockup-stat-label">Saved this month</span>
                </div>
                <div className="mockup-stat-divider" />
                <div className="mockup-stat">
                  <span className="mockup-stat-value mockup-stat-value--warning">78%</span>
                  <span className="mockup-stat-label">Budget utilized</span>
                </div>
              </div>

              <div className="mockup-insight-banner">
                <span className="mockup-ai-pill">AI</span>
                <span className="mockup-insight-text">
                  Food delivery spending increased 18% this month — ₹8,200 of ₹10,000 budget used
                </span>
              </div>

              <div className="mockup-section-label">Recent transactions</div>
              <div className="mockup-txns">
                {TRANSACTIONS.map((t, i) => (
                  <div className="mockup-txn" key={i}>
                    <div className="mockup-txn-left">
                      <span className="mockup-txn-merchant">{t.merchant}</span>
                      <span className="mockup-txn-cat">{t.category}</span>
                    </div>
                    <span className={`mockup-txn-amount ${t.positive ? 'mockup-txn-amount--pos' : ''}`}>
                      {t.amount}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="hero-float-card">
            <div className="float-card-header">
              <span className="float-card-tag float-card-tag--blue">Pattern detected</span>
            </div>
            <p className="float-card-text">
              Your weekend discretionary spending is 42% higher than weekdays.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
