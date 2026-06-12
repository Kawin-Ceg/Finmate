import './HealthScoreCard.css';

const CIRCUMFERENCE = 2 * Math.PI * 54;

const BREAKDOWN_ROWS = [
  ['Savings Rate',      'savings_rate',      'savings_rate_max'],
  ['Expense Stability', 'expense_stability', 'expense_stability_max'],
  ['Income Consistency','income_consistency','income_consistency_max'],
  ['Diversification',   'diversification',   'diversification_max'],
];

function scoreColor(score) {
  if (score >= 80) return '#10B981';
  if (score >= 60) return '#F59E0B';
  return '#EF4444';
}

export default function HealthScoreCard({ data, loading }) {
  const score = data?.score ?? 0;
  const color = scoreColor(score);
  const dashOffset = loading ? CIRCUMFERENCE : CIRCUMFERENCE * (1 - score / 100);

  return (
    <div className="health-card">
      <div className="health-card-header">
        <h2 className="health-card-title">Financial Health Score</h2>
        <p className="health-card-sub">Based on your transaction history</p>
      </div>

      <div className="health-card-body">
        <div className="health-ring-wrap">
          <svg className="health-ring" viewBox="0 0 148 148">
            <circle
              cx="74" cy="74" r="54"
              fill="none" stroke="#F1F5F9" strokeWidth="8"
            />
            <circle
              cx="74" cy="74" r="54"
              fill="none"
              stroke={loading ? '#E2E8F0' : color}
              strokeWidth="8"
              strokeDasharray={CIRCUMFERENCE}
              strokeDashoffset={dashOffset}
              strokeLinecap="round"
              transform="rotate(-90 74 74)"
              style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.4,0,0.2,1)' }}
            />
          </svg>
          <div className="health-ring-inner">
            <span className="health-ring-score">{loading ? '—' : score}</span>
            <span className="health-ring-grade">{loading ? '' : (data?.grade ?? '')}</span>
          </div>
        </div>

        <span
          className="health-status-badge"
          style={
            loading
              ? { background: '#F1F5F9', color: '#94A3B8' }
              : { background: color + '1A', color }
          }
        >
          {loading ? 'Computing…' : (data?.status ?? '—')}
        </span>

        <div className="health-breakdown">
          {BREAKDOWN_ROWS.map(([label, key, maxKey]) => {
            const val = data?.breakdown?.[key] ?? 0;
            const max = data?.breakdown?.[maxKey] ?? 1;
            return (
              <div key={label} className="health-bd-row">
                <span className="health-bd-label">{label}</span>
                <div className="health-bd-track">
                  <div
                    className="health-bd-fill"
                    style={{ width: loading ? '0%' : `${(val / max) * 100}%`, background: color }}
                  />
                </div>
                <span className="health-bd-score">
                  {loading ? '—' : `${val}/${max}`}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
