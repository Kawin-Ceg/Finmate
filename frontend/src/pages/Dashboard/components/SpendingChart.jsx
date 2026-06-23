import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { BarChart2 } from 'lucide-react';
import './SpendingChart.css';

const CATEGORY_COLORS = [
  '#2563EB', '#10B981', '#F59E0B', '#8B5CF6',
  '#EF4444', '#06B6D4', '#F97316', '#EC4899',
];

const fmt = (v) => `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
const fmtK = (v) => `₹${(v / 1000).toFixed(0)}k`;

function CustomTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="sc-tooltip">
      <span className="sc-tooltip-label">{label}</span>
      <span className="sc-tooltip-val">{fmt(payload[0].value)}</span>
    </div>
  );
}

function Skeleton() {
  return (
    <div className="sc-skeleton-wrap">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="sc-skel-row">
          <div className="sc-skel sc-skel--label" />
          <div className="sc-skel sc-skel--bar" style={{ width: `${85 - i * 10}%` }} />
        </div>
      ))}
    </div>
  );
}

export default function SpendingChart({ loading, trend, categories, overview }) {
  const trendData = trend?.data || [];
  const latest = trendData[trendData.length - 1];
  const catData = (categories?.data || []).slice(0, 5);
  const catMax = catData[0]?.percentage || 1;

  return (
    <div className="sc-card">
      <div className="sc-card-header">
        <div className="sc-header-left">
          <BarChart2 size={14} strokeWidth={2} className="sc-header-icon" />
          <div>
            <h2 className="sc-card-title">Spending Intelligence</h2>
            <p className="sc-card-subtitle">Monthly trend · top categories</p>
          </div>
        </div>
        <span className="sc-engine-badge">Analytics Engine</span>
      </div>

      {loading ? (
        <div className="sc-loading">
          <Skeleton />
        </div>
      ) : (
        <div className="sc-body">

          {/* Trend chart */}
          <div className="sc-trend">
            <div className="sc-sub-header">
              <span className="sc-sub-title">Monthly Spending</span>
              {latest && <span className="sc-sub-val">{fmt(latest.spending)} this month</span>}
            </div>
            <ResponsiveContainer width="100%" height={170}>
              <AreaChart data={trendData} margin={{ top: 8, right: 4, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="trendGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#2563EB" stopOpacity={0.1} />
                    <stop offset="95%" stopColor="#2563EB" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="month" tick={{ fontSize: 11, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} dy={5} />
                <YAxis tickFormatter={fmtK} tick={{ fontSize: 11, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} width={40} />
                <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'var(--border)', strokeWidth: 1 }} />
                <Area type="monotone" dataKey="spending" stroke="#2563EB" strokeWidth={1.75} fill="url(#trendGrad)" dot={false} activeDot={{ r: 3.5, fill: '#2563EB', strokeWidth: 0 }} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {/* Category breakdown */}
          <div className="sc-cats">
            <div className="sc-sub-header">
              <span className="sc-sub-title">Top Categories</span>
              {overview && <span className="sc-sub-val">{fmt(overview.expense)} total</span>}
            </div>
            <div className="sc-cat-list">
              {catData.map((cat, i) => (
                <div key={cat.category} className="sc-cat-row">
                  <div className="sc-cat-info">
                    <span className="sc-cat-dot" style={{ background: CATEGORY_COLORS[i % CATEGORY_COLORS.length] }} />
                    <span className="sc-cat-name">{cat.category}</span>
                  </div>
                  <div className="sc-cat-bar-track">
                    <div
                      className="sc-cat-bar-fill"
                      style={{ width: `${(cat.percentage / catMax) * 100}%`, background: CATEGORY_COLORS[i % CATEGORY_COLORS.length] }}
                    />
                  </div>
                  <span className="sc-cat-pct">{cat.percentage.toFixed(0)}%</span>
                  <span className="sc-cat-amt">{fmt(cat.amount)}</span>
                </div>
              ))}
            </div>
          </div>

        </div>
      )}
    </div>
  );
}
