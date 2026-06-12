import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

function formatY(v) {
  if (v >= 100000) return `₹${(v / 100000).toFixed(1)}L`;
  if (v >= 1000) return `₹${(v / 1000).toFixed(0)}k`;
  return `₹${v}`;
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip">
      <span className="chart-tooltip-label">{label}</span>
      {payload.map(p => (
        <div key={p.dataKey} className="an-tooltip-row">
          <span className="an-tooltip-dot" style={{ background: p.fill }} />
          <span style={{ fontSize: 13, color: 'var(--text)', fontWeight: 500 }}>
            {p.name}: ₹{p.value.toLocaleString('en-IN')}
          </span>
        </div>
      ))}
    </div>
  );
}

export default function CashflowChart({ data, loading }) {
  return (
    <div className="an-card">
      <div className="an-card-header">
        <div>
          <h2 className="an-card-title">Monthly Cashflow</h2>
          <p className="an-card-sub">Income vs Expenses per month</p>
        </div>
        <div className="cf-legend">
          <span className="cf-dot cf-dot--income" />
          <span className="cf-label">Income</span>
          <span className="cf-dot cf-dot--expense" />
          <span className="cf-label">Expense</span>
        </div>
      </div>
      <div className="an-card-body">
        {loading ? (
          <div className="an-chart-skeleton" style={{ height: 260 }} />
        ) : data.length === 0 ? (
          <div className="an-chart-empty" style={{ height: 260 }}>No cashflow data yet</div>
        ) : (
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={data} margin={{ top: 8, right: 4, left: 0, bottom: 0 }} barCategoryGap="35%">
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" vertical={false} />
              <XAxis
                dataKey="month"
                tick={{ fontSize: 12, fill: '#94A3B8' }}
                axisLine={false} tickLine={false} dy={6}
              />
              <YAxis
                tickFormatter={formatY}
                tick={{ fontSize: 12, fill: '#94A3B8' }}
                axisLine={false} tickLine={false} width={52}
              />
              <Tooltip
                content={<CustomTooltip />}
                cursor={{ fill: 'rgba(0,0,0,0.025)' }}
              />
              <Bar dataKey="income" name="Income" fill="#10B981" radius={[3, 3, 0, 0]} maxBarSize={28} />
              <Bar dataKey="expense" name="Expense" fill="#EF4444" radius={[3, 3, 0, 0]} maxBarSize={28} />
            </BarChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
