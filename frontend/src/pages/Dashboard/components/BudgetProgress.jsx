import './BudgetProgress.css';

const BUDGETS = [
  {
    category: 'Food & Dining',
    spent: 8200,
    limit: 10000,
    color: '#2563EB',
  },
  {
    category: 'Transportation',
    spent: 3100,
    limit: 5000,
    color: '#10B981',
  },
  {
    category: 'Entertainment',
    spent: 2800,
    limit: 3000,
    color: '#F59E0B',
  },
  {
    category: 'Utilities',
    spent: 4500,
    limit: 6000,
    color: '#8B5CF6',
  },
];

function formatINR(amount) {
  return `₹${amount.toLocaleString('en-IN')}`;
}

export default function BudgetProgress() {
  return (
    <div className="budget-card">
      <div className="budget-header">
        <div>
          <h2 className="budget-title">Budget Tracking</h2>
          <p className="budget-subtitle">June 2025</p>
        </div>
      </div>

      <div className="budget-list">
        {BUDGETS.map((item) => {
          const pct = Math.min((item.spent / item.limit) * 100, 100);
          const remaining = item.limit - item.spent;
          const isOver = item.spent > item.limit;

          return (
            <div key={item.category} className="budget-item">
              <div className="budget-item-top">
                <span className="budget-cat">{item.category}</span>
                <div className="budget-amounts">
                  <span className="budget-spent">{formatINR(item.spent)}</span>
                  <span className="budget-separator">/</span>
                  <span className="budget-limit">{formatINR(item.limit)}</span>
                </div>
              </div>

              <div className="budget-bar-wrap">
                <div className="budget-bar">
                  <div
                    className="budget-bar-fill"
                    style={{
                      width: `${pct}%`,
                      background: isOver ? '#EF4444' : item.color,
                    }}
                  />
                </div>
                <span
                  className={`budget-pct ${isOver ? 'budget-pct--over' : ''}`}
                >
                  {Math.round(pct)}%
                </span>
              </div>

              <div className="budget-remaining">
                {isOver ? (
                  <span className="budget-over">
                    Over by {formatINR(Math.abs(remaining))}
                  </span>
                ) : (
                  <span>{formatINR(remaining)} remaining</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
