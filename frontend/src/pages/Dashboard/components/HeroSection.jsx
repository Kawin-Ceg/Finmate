import { Activity } from 'lucide-react';
import './HeroSection.css';

const GRADE_COLOR = { 'A+': 'green', A: 'green', B: 'blue', C: 'yellow', D: 'red' };

function Metric({ label, value, sub, accent, loading }) {
  return (
    <div className={`hero-metric hero-metric--${accent}`}>
      <span className="hero-metric-label">{label}</span>
      <span className="hero-metric-value">
        {loading ? <span className="hero-skeleton hero-skeleton--val" /> : value}
      </span>
      <span className="hero-metric-sub">
        {loading ? <span className="hero-skeleton hero-skeleton--sub" /> : sub}
      </span>
    </div>
  );
}

export default function HeroSection({ loading, healthScore, overview, budgetRiskCount, criticalCount, anomalyCount }) {
  const score = healthScore?.score ?? null;
  const grade = healthScore?.grade ?? null;
  const status = healthScore?.status ?? null;
  const savingsRate = overview?.savings_rate ?? null;
  const savings = overview?.savings ?? null;
  const gradeAccent = grade ? (GRADE_COLOR[grade] || 'blue') : 'blue';

  return (
    <div className="hero-section">
      <div className="hero-section-header">
        <div className="hero-section-title-row">
          <Activity size={14} strokeWidth={2} className="hero-header-icon" />
          <span className="hero-section-title">Financial Intelligence Overview</span>
        </div>
        <span className="hero-section-sub">All metrics computed from your transaction history</span>
      </div>

      <div className="hero-metrics-row">
        <div className={`hero-score-block hero-score-block--${gradeAccent}`}>
          <span className="hero-score-num">
            {loading ? <span className="hero-skeleton hero-skeleton--score" /> : (score ?? '—')}
          </span>
          <div className="hero-score-meta">
            <span className={`hero-grade-badge hero-grade-badge--${gradeAccent}`}>
              {loading ? '—' : (grade ?? '—')}
            </span>
            <span className="hero-score-label">
              {loading ? 'Computing…' : (status ?? 'Health Score')}
            </span>
          </div>
        </div>

        {/* The divider column (1px) is a CSS grid cell — no extra div needed */}
        <div className="hero-divider" />

        <Metric
          label="Savings Rate"
          value={loading ? null : (savingsRate !== null ? `${savingsRate.toFixed(1)}%` : '—')}
          sub={loading ? null : (savings !== null ? `₹${Number(savings).toLocaleString('en-IN', { maximumFractionDigits: 0 })} saved` : null)}
          accent={savingsRate !== null ? (savingsRate >= 20 ? 'green' : savingsRate >= 10 ? 'yellow' : 'red') : 'neutral'}
          loading={loading}
        />

        <Metric
          label="Budget Risks"
          value={loading ? null : String(budgetRiskCount)}
          sub={loading ? null : (budgetRiskCount === 0 ? 'All budgets safe' : `${budgetRiskCount} need attention`)}
          accent={budgetRiskCount > 0 ? (budgetRiskCount > 2 ? 'red' : 'yellow') : 'green'}
          loading={loading}
        />

        <Metric
          label="Critical Anomalies"
          value={loading ? null : String(criticalCount)}
          sub={loading ? null : (anomalyCount > 0 ? `${anomalyCount} total detected` : 'None detected')}
          accent={criticalCount > 0 ? 'red' : (anomalyCount > 0 ? 'yellow' : 'green')}
          loading={loading}
        />
      </div>
    </div>
  );
}
