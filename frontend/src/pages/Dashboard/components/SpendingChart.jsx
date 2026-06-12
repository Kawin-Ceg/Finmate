import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import './SpendingChart.css';

const DATA = [
  { month: 'Jan', amount: 38200 },
  { month: 'Feb', amount: 41500 },
  { month: 'Mar', amount: 39800 },
  { month: 'Apr', amount: 44200 },
  { month: 'May', amount: 43600 },
  { month: 'Jun', amount: 47280 },
];

function formatYAxis(value) {
  return `₹${(value / 1000).toFixed(0)}k`;
}

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;
  return (
    <div className="chart-tooltip">
      <span className="chart-tooltip-label">{label}</span>
      <span className="chart-tooltip-value">
        ₹{payload[0].value.toLocaleString('en-IN')}
      </span>
    </div>
  );
}

export default function SpendingChart() {
  return (
    <div className="chart-card">
      <div className="chart-header">
        <div>
          <h2 className="chart-title">Monthly Spending Trend</h2>
          <p className="chart-subtitle">Jan – Jun 2025</p>
        </div>
        <div className="chart-stat">
          <span className="chart-stat-value">₹47,280</span>
          <span className="chart-stat-label">this month</span>
        </div>
      </div>

      <div className="chart-body">
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart
            data={DATA}
            margin={{ top: 8, right: 4, left: 0, bottom: 0 }}
          >
            <defs>
              <linearGradient id="spendGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#2563EB" stopOpacity={0.1} />
                <stop offset="95%" stopColor="#2563EB" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="#F1F5F9"
              vertical={false}
            />
            <XAxis
              dataKey="month"
              tick={{ fontSize: 12, fill: '#94A3B8' }}
              axisLine={false}
              tickLine={false}
              dy={6}
            />
            <YAxis
              tickFormatter={formatYAxis}
              tick={{ fontSize: 12, fill: '#94A3B8' }}
              axisLine={false}
              tickLine={false}
              width={44}
            />
            <Tooltip
              content={<CustomTooltip />}
              cursor={{ stroke: '#E2E8F0', strokeWidth: 1 }}
            />
            <Area
              type="monotone"
              dataKey="amount"
              stroke="#2563EB"
              strokeWidth={1.75}
              fill="url(#spendGrad)"
              dot={false}
              activeDot={{ r: 4, fill: '#2563EB', strokeWidth: 0 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
