import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';

const CATEGORY_COLORS = {
  Food:          '#F59E0B',
  Transport:     '#2563EB',
  Shopping:      '#8B5CF6',
  Utilities:     '#10B981',
  Entertainment: '#EF4444',
  Health:        '#06B6D4',
  Cash:          '#F97316',
  Transfers:     '#3B82F6',
  Insurance:     '#A855F7',
  Investment:    '#059669',
  Education:     '#D97706',
  Rent:          '#DC2626',
  Subscriptions: '#7C3AED',
  Income:        '#10B981',
  Other:         '#94A3B8',
};

const FALLBACK = ['#2563EB','#10B981','#F59E0B','#EF4444','#8B5CF6','#06B6D4','#F97316','#EC4899'];

function CustomTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const d = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <span className="chart-tooltip-label">{d.category}</span>
      <span className="chart-tooltip-value">
        ₹{d.amount.toLocaleString('en-IN')} · {d.percentage}%
      </span>
    </div>
  );
}

export default function CategoryBreakdownChart({ data, loading }) {
  return (
    <div className="an-card">
      <div className="an-card-header">
        <div>
          <h2 className="an-card-title">Spending by Category</h2>
          <p className="an-card-sub">Where your money goes</p>
        </div>
      </div>
      <div className="an-card-body">
        {loading ? (
          <div className="an-chart-skeleton" style={{ height: 220 }} />
        ) : data.length === 0 ? (
          <div className="an-chart-empty" style={{ height: 220 }}>No expense data yet</div>
        ) : (
          <>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  innerRadius={58}
                  outerRadius={88}
                  paddingAngle={2}
                  dataKey="amount"
                  strokeWidth={0}
                >
                  {data.map((entry, i) => (
                    <Cell
                      key={entry.category}
                      fill={CATEGORY_COLORS[entry.category] || FALLBACK[i % FALLBACK.length]}
                    />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              </PieChart>
            </ResponsiveContainer>
            <div className="cat-legend">
              {data.slice(0, 8).map((d, i) => (
                <div key={d.category} className="cat-legend-item">
                  <span
                    className="cat-legend-dot"
                    style={{ background: CATEGORY_COLORS[d.category] || FALLBACK[i % FALLBACK.length] }}
                  />
                  <span className="cat-legend-name">{d.category}</span>
                  <span className="cat-legend-pct">{d.percentage}%</span>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
