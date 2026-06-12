import {
  AreaChart,
  Area,
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
      <span className="chart-tooltip-value">
        ₹{payload[0].value.toLocaleString('en-IN')}
      </span>
    </div>
  );
}

export default function MonthlyTrendChart({ data, loading }) {
  return (
    <div className="an-card">
      <div className="an-card-header">
        <div>
          <h2 className="an-card-title">Monthly Spending Trend</h2>
          <p className="an-card-sub">Your expense pattern over time</p>
        </div>
        {data.length > 0 && !loading && (
          <div style={{ textAlign: 'right', flexShrink: 0 }}>
            <div style={{ fontSize: 20, fontWeight: 600, color: 'var(--text)', letterSpacing: '-0.02em' }}>
              ₹{data[data.length - 1]?.spending.toLocaleString('en-IN')}
            </div>
            <div style={{ fontSize: 11.5, color: 'var(--text-muted)', marginTop: 1 }}>
              {data[data.length - 1]?.month}
            </div>
          </div>
        )}
      </div>
      <div className="an-card-body">
        {loading ? (
          <div className="an-chart-skeleton" style={{ height: 240 }} />
        ) : data.length === 0 ? (
          <div className="an-chart-empty" style={{ height: 240 }}>No spending data yet</div>
        ) : (
          <ResponsiveContainer width="100%" height={240}>
            <AreaChart data={data} margin={{ top: 8, right: 4, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#2563EB" stopOpacity={0.1} />
                  <stop offset="95%" stopColor="#2563EB" stopOpacity={0} />
                </linearGradient>
              </defs>
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
                cursor={{ stroke: '#E2E8F0', strokeWidth: 1 }}
              />
              <Area
                type="monotone"
                dataKey="spending"
                stroke="#2563EB"
                strokeWidth={1.75}
                fill="url(#trendGrad)"
                dot={false}
                activeDot={{ r: 4, fill: '#2563EB', strokeWidth: 0 }}
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
