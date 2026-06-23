import './HealthScoreCard.css';

const COMPONENTS = [
  { key: 'savings_rate',       maxKey: 'savings_rate_max',       label: 'Savings Rate',        color: 'blue'   },
  { key: 'income_consistency', maxKey: 'income_consistency_max', label: 'Income Consistency',  color: 'green'  },
  { key: 'expense_stability',  maxKey: 'expense_stability_max',  label: 'Expense Stability',   color: 'purple' },
  { key: 'diversification',    maxKey: 'diversification_max',    label: 'Diversification',     color: 'yellow' },
];

function scoreAccent(score) {
  if (score >= 80) return 'green';
  if (score >= 60) return 'blue';
  if (score >= 40) return 'yellow';
  return 'red';
}

function ScoreRing({ score, grade, loading }) {
  const radius = 58;
  const circ = 2 * Math.PI * radius;
  const pct = loading ? 0 : Math.min(100, Math.max(0, score ?? 0));
  const offset = circ - (pct / 100) * circ;
  const accent = scoreAccent(score ?? 0);

  const ringColor =
    accent === 'green'  ? 'var(--green)'   :
    accent === 'blue'   ? 'var(--primary)' :
    accent === 'yellow' ? 'var(--yellow)'  : 'var(--red)';

  return (
    <div className={`hs-ring-wrap hs-ring-wrap--${accent}`}>
      <svg width="140" height="140" viewBox="0 0 140 140" className="hs-ring-svg">
        <circle cx="70" cy="70" r={radius} fill="none" stroke="var(--border)" strokeWidth="11" />
        <circle
          cx="70" cy="70" r={radius}
          fill="none"
          stroke={ringColor}
          strokeWidth="11"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={offset}
          transform="rotate(-90 70 70)"
          style={{ transition: 'stroke-dashoffset 0.9s cubic-bezier(0.4,0,0.2,1)', filter: `drop-shadow(0 0 6px ${ringColor}88)` }}
        />
      </svg>
      <div className="hs-ring-center">
        <span className="hs-ring-score">{loading ? '—' : (score ?? '—')}</span>
        <span className={`hs-ring-grade hs-ring-grade--${accent}`}>{loading ? '' : (grade ?? '')}</span>
      </div>
    </div>
  );
}

function ComponentBar({ label, score, max, color, loading }) {
  const pct = max > 0 ? Math.min(100, (score / max) * 100) : 0;
  return (
    <div className="hs-comp-row">
      <div className="hs-comp-header">
        <span className="hs-comp-label">{label}</span>
        <span className="hs-comp-pts">
          {loading ? '—' : `${score?.toFixed(0) ?? 0} / ${max}`}
        </span>
      </div>
      <div className="hs-comp-bar-track">
        <div
          className={`hs-comp-bar-fill hs-comp-bar-fill--${color}`}
          style={{ width: loading ? '0%' : `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function HealthScoreCard({ loading, healthScore }) {
  const bd = healthScore?.breakdown;
  const insights = healthScore?.insights || [];
  const accent = loading ? 'blue' : scoreAccent(healthScore?.score ?? 0);

  return (
    <div className={`hs-card hs-card--${accent}`}>
      <div className="hs-card-header">
        <div>
          <h2 className="hs-card-title">Financial Health Score</h2>
          <p className="hs-card-subtitle">Weighted across 4 financial dimensions</p>
        </div>
        <span className={`hs-engine-badge hs-engine-badge--${accent}`}>Health Engine</span>
      </div>

      <div className="hs-card-body">
        <div className="hs-left">
          <ScoreRing score={healthScore?.score} grade={healthScore?.grade} loading={loading} />
          <div className="hs-status-row">
            <span className="hs-status-label">Status</span>
            <span className={`hs-status-value hs-status-value--${accent}`}>
              {loading ? '—' : (healthScore?.status ?? '—')}
            </span>
          </div>
        </div>

        <div className="hs-right">
          <div className="hs-components">
            {COMPONENTS.map((c) => (
              <ComponentBar
                key={c.key}
                label={c.label}
                score={bd?.[c.key] ?? 0}
                max={bd?.[c.maxKey] ?? 1}
                color={c.color}
                loading={loading}
              />
            ))}
          </div>

          {insights.length > 0 && (
            <div className="hs-insights">
              {insights.slice(0, 2).map((ins, i) => (
                <div key={i} className="hs-insight-item">
                  <span className={`hs-insight-dot hs-insight-dot--${accent}`} />
                  <span className="hs-insight-text">{ins}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
