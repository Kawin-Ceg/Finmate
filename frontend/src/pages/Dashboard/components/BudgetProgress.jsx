import { Target } from 'lucide-react';
import './BudgetProgress.css';

const RISK_CONFIG = {
  safe:     { label: 'Safe',     accent: 'green'  },
  watch:    { label: 'Watch',    accent: 'yellow' },
  high:     { label: 'High',     accent: 'orange' },
  exceeded: { label: 'Exceeded', accent: 'red'    },
};

const fmt = (v) => `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;

function BudgetRow({ f }) {
  const currentPct = f.budget > 0 ? Math.min(100, (f.current_spend / f.budget) * 100) : 0;
  const projPct    = f.budget > 0 ? Math.min(110, (f.projected_spend / f.budget) * 100) : 0;
  const cfg = RISK_CONFIG[f.risk] || RISK_CONFIG.safe;
  const isOver = f.risk === 'exceeded' || f.risk === 'high';

  return (
    <div className="bp-row">
      <div className="bp-row-header">
        <span className="bp-category">{f.category}</span>
        <span className={`bp-risk-badge bp-risk-badge--${cfg.accent}`}>{cfg.label}</span>
      </div>

      <div className="bp-bar-group">
        <div className="bp-bar-label-row">
          <span className="bp-bar-label">Current</span>
          <span className="bp-bar-val">{fmt(f.current_spend)} / {fmt(f.budget)}</span>
        </div>
        <div className="bp-track">
          <div
            className={`bp-fill bp-fill--current${isOver ? ' bp-fill--danger' : ''}`}
            style={{ width: `${currentPct}%` }}
          />
        </div>

        <div className="bp-bar-label-row">
          <span className="bp-bar-label bp-bar-label--proj">Projected EOm</span>
          <span className={`bp-bar-val${isOver ? ' bp-bar-val--danger' : ''}`}>{fmt(f.projected_spend)}</span>
        </div>
        <div className="bp-track">
          <div
            className={`bp-fill bp-fill--projected${isOver ? ' bp-fill--danger' : ''}`}
            style={{ width: `${Math.min(100, projPct)}%` }}
          />
          {projPct > 100 && (
            <div className="bp-overrun-marker" style={{ left: `calc(100% - 2px)` }} />
          )}
        </div>
      </div>

      <div className="bp-row-footer">
        {f.risk === 'exceeded' ? (
          <span className="bp-overrun-text">Over by {fmt(f.expected_overrun)}</span>
        ) : f.expected_overrun > 0 ? (
          <span className="bp-proj-text">{fmt(f.expected_overrun)} overrun projected · {f.days_remaining}d left</span>
        ) : (
          <span className="bp-safe-text">{fmt(f.budget - f.current_spend)} remaining · {f.days_remaining}d left</span>
        )}
      </div>
    </div>
  );
}

function SkeletonRow() {
  return (
    <div className="bp-row">
      <div className="bp-skel-header">
        <div className="bp-skel bp-skel--cat" />
        <div className="bp-skel bp-skel--badge" />
      </div>
      <div className="bp-skel bp-skel--bar" />
      <div className="bp-skel bp-skel--bar" style={{ marginTop: 8, opacity: 0.6 }} />
    </div>
  );
}

export default function BudgetProgress({ loading, forecast }) {
  const forecasts = forecast?.forecasts || [];
  const sorted = [...forecasts]
    .sort((a, b) => {
      const order = { exceeded: 0, high: 1, watch: 2, safe: 3 };
      return (order[a.risk] ?? 99) - (order[b.risk] ?? 99);
    })
    .slice(0, 4);

  const riskCount = forecasts.filter((f) => f.risk === 'high' || f.risk === 'exceeded').length;

  return (
    <div className="bp-card">
      <div className="bp-card-header">
        <div className="bp-header-left">
          <Target size={14} strokeWidth={2} className="bp-header-icon" />
          <div>
            <h2 className="bp-title">Budget Risk Panel</h2>
            <p className="bp-subtitle">
              {loading
                ? 'Loading forecast…'
                : sorted.length === 0
                ? 'No budgets configured'
                : `${sorted.length} budget${sorted.length !== 1 ? 's' : ''} · ${riskCount} at risk · current + projected`}
            </p>
          </div>
        </div>
        <span className="bp-engine-badge">Forecast Engine</span>
      </div>

      <div className="bp-list">
        {loading
          ? Array.from({ length: 3 }).map((_, i) => <SkeletonRow key={i} />)
          : sorted.length === 0
          ? (
            <div className="bp-empty">
              <p>No budgets set. Create budgets to enable forecasting.</p>
            </div>
          )
          : sorted.map((f) => <BudgetRow key={f.category} f={f} />)
        }
      </div>
    </div>
  );
}
