import './AIShowcase.css';

const INSIGHTS = [
  {
    type: 'warning',
    label: 'Spending alert',
    title: 'Food delivery up 18% this month',
    body: 'You\'ve spent ₹8,200 on food delivery in June — ₹1,240 more than May. At this pace you\'ll exceed your ₹10,000 budget in 4 days.',
    action: 'Review food spending',
  },
  {
    type: 'info',
    label: 'Pattern detected',
    title: 'Subscriptions at 11% of income',
    body: '7 active subscriptions detected totalling ₹2,847/month. Netflix, Spotify, Amazon Prime, and 4 others are auto-debiting monthly.',
    action: 'See all subscriptions',
  },
  {
    type: 'success',
    label: 'Savings opportunity',
    title: 'On track to save ₹15,000',
    body: 'Your transportation spending is 38% below budget this month. If current patterns hold, you\'ll save ₹15,000 by month end.',
    action: 'View savings projection',
  },
];

const TYPE_META = {
  warning: { border: '#F59E0B', badge: '#FFFBEB', badgeText: '#92400E', dot: '#F59E0B' },
  info:    { border: '#2563EB', badge: '#EFF6FF', badgeText: '#1D4ED8', dot: '#2563EB' },
  success: { border: '#10B981', badge: '#ECFDF5', badgeText: '#065F46', dot: '#10B981' },
};

export default function AIShowcase() {
  return (
    <section className="ai-section">
      <div className="ai-inner">
        <div className="ai-header">
          <span className="ai-eyebrow">AI insights</span>
          <h2 className="ai-title">AI that speaks your financial language</h2>
          <p className="ai-sub">
            FinMate doesn&apos;t just show you charts. It tells you what they mean —
            and what to do about it.
          </p>
        </div>

        <div className="ai-cards">
          {INSIGHTS.map((ins) => {
            const meta = TYPE_META[ins.type];
            return (
              <div
                key={ins.title}
                className="ai-card"
                style={{ borderTopColor: meta.border }}
              >
                <div className="ai-card-top">
                  <span
                    className="ai-card-badge"
                    style={{ background: meta.badge, color: meta.badgeText }}
                  >
                    <span
                      className="ai-card-dot"
                      style={{ background: meta.dot }}
                    />
                    {ins.label}
                  </span>
                  <span className="ai-card-ai-tag">AI</span>
                </div>
                <h3 className="ai-card-title">{ins.title}</h3>
                <p className="ai-card-body">{ins.body}</p>
                <button className="ai-card-action">
                  {ins.action}
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <path d="M2.5 6H9.5M9.5 6L6.5 3M9.5 6L6.5 9" stroke="currentColor" strokeWidth="1.25" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </button>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
