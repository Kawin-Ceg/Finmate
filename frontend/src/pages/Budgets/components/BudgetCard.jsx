import { Pencil, Trash2 } from 'lucide-react';
import { deleteBudget } from '../../../services/budgetService';
import './BudgetCard.css';

const RISK_CONFIG = {
  safe:     { label: 'On Track', color: '#10B981', bg: '#ECFDF5', border: '#10B981' },
  watch:    { label: 'Watch',    color: '#F59E0B', bg: '#FFFBEB', border: '#F59E0B' },
  high:     { label: 'At Risk',  color: '#F97316', bg: '#FFF7ED', border: '#F97316' },
  exceeded: { label: 'Exceeded', color: '#EF4444', bg: '#FEF2F2', border: '#EF4444' },
};

function formatINR(v) {
  return `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
}

export default function BudgetCard({ budget, onEdit, onDeleted }) {
  const risk = RISK_CONFIG[budget.risk] || RISK_CONFIG.safe;
  const pctClamped = Math.min(budget.pct_used, 100);

  const handleDelete = async () => {
    if (!window.confirm(`Delete budget for ${budget.category}?`)) return;
    try {
      await deleteBudget(budget.id);
      onDeleted();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className={`bc bc--${budget.risk}`}>
      <div className="bc-header">
        <div className="bc-category-row">
          <span className="bc-dot" style={{ background: risk.color }} />
          <span className="bc-category">{budget.category}</span>
        </div>
        <div className="bc-actions">
          <button
            className="bc-btn"
            onClick={() => onEdit(budget)}
            title="Edit budget"
            aria-label="Edit budget"
          >
            <Pencil size={12} strokeWidth={2} />
          </button>
          <button
            className="bc-btn bc-btn--danger"
            onClick={handleDelete}
            title="Delete budget"
            aria-label="Delete budget"
          >
            <Trash2 size={12} strokeWidth={2} />
          </button>
        </div>
      </div>

      <div className="bc-amounts">
        <div>
          <div className="bc-spent-label">Spent this month</div>
          <div className="bc-spent-value">{formatINR(budget.current_spend)}</div>
        </div>
        <div className="bc-limit-block">
          <div className="bc-limit-label">of</div>
          <div className="bc-limit-value">{formatINR(budget.monthly_limit)}</div>
        </div>
      </div>

      <div className="bc-progress-wrap">
        <div className="bc-track">
          <div
            className="bc-fill"
            style={{ width: `${pctClamped}%`, background: risk.color }}
          />
        </div>
        <span className="bc-pct">{budget.pct_used}%</span>
      </div>

      <div className="bc-footer">
        <span className="bc-badge" style={{ color: risk.color, background: risk.bg }}>
          {risk.label}
        </span>
        <span className="bc-remaining">
          {budget.remaining >= 0
            ? `${formatINR(budget.remaining)} left`
            : `${formatINR(Math.abs(budget.remaining))} over`}
        </span>
      </div>
    </div>
  );
}
