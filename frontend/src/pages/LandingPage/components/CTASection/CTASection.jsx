import './CTASection.css';

export default function CTASection() {
  return (
    <section className="cta-section">
      <div className="cta-inner">
        <div className="cta-content">
          <span className="cta-eyebrow">Get started</span>
          <h2 className="cta-title">
            Start understanding your money,
            <br />
            not just tracking it.
          </h2>
          <p className="cta-sub">
            Experience financial clarity powered by AI.
            No spreadsheets. No manual tagging. Just insight.
          </p>
          <div className="cta-actions">
            <a href="/signup" className="cta-btn-primary">
              Create free account
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M3 7H11M11 7L7.5 3.5M11 7L7.5 10.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </a>
            <a href="/login" className="cta-btn-secondary">
              Log in
            </a>
          </div>
          <p className="cta-footnote"></p>
        </div>
      </div>
    </section>
  );
}
