import { useState, useEffect, useCallback } from 'react';
import {
  AlertTriangle,
  TrendingUp,
  PieChart,
  Store,
  RefreshCw,
  Wallet,
  ShieldCheck,
  RotateCcw,
  Lightbulb,
  Calendar,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, Tooltip,
  ResponsiveContainer, Cell,
} from 'recharts';
import Topbar from '../Dashboard/components/Topbar';
import StatsCard from '../Dashboard/components/StatsCard';
import {
  getAnomalies,
  getAnomalySummary,
  getAnomalyStats,
  getSubscriptions,
  runAnomalyDetection,
} from '../../services/anomalyService';
import './AnomaliesPage.css';

// ── Helpers ──────────────────────────────────────────────────────────────────

function fmt(v, decimals = 0) {
  if (v === null || v === undefined) return '₹—';
  return `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: decimals })}`;
}

function timeAgo(dateStr) {
  if (!dateStr) return '';
  const diff = Math.floor((Date.now() - new Date(dateStr)) / 1000);
  if (diff < 60) return 'just now';
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

const TYPE_META = {
  transaction:  { label: 'Transaction',   Icon: TrendingUp,  color: '#8b5cf6' },
  category:     { label: 'Category',      Icon: PieChart,    color: '#3b82f6' },
  merchant:     { label: 'Merchant',      Icon: Store,       color: '#f59e0b' },
  subscription: { label: 'Subscription',  Icon: RefreshCw,   color: '#10b981' },
  budget:       { label: 'Budget Risk',   Icon: Wallet,      color: '#ef4444' },
};

const SEV_META = {
  critical: { label: 'Critical', bg: '#fee2e2', color: '#b91c1c', bar: '#ef4444' },
  high:     { label: 'High',     bg: '#ffedd5', color: '#c2410c', bar: '#f97316' },
  medium:   { label: 'Medium',   bg: '#fef9c3', color: '#92400e', bar: '#f59e0b' },
  low:      { label: 'Low',      bg: '#dbeafe', color: '#1e40af', bar: '#3b82f6' },
};

const BORDER_COLOR = {
  critical: '#ef4444',
  high: '#f97316',
  medium: '#f59e0b',
  low: '#3b82f6',
};

function getCardStats(type, meta) {
  if (!meta) return [];
  switch (type) {
    case 'transaction':
      return [
        { label: 'Expected Range', value: `${fmt(meta.expected_range_min)}–${fmt(meta.expected_range_max)}` },
        { label: 'Actual Amount',  value: fmt(meta.transaction_amount) },
        { label: 'Deviation',      value: `+${meta.deviation_pct ?? 0}%` },
      ];
    case 'category':
      return [
        { label: 'Historical Avg', value: `${fmt(meta.historical_avg)}/mo` },
        { label: 'This Month',     value: fmt(meta.current_month_spend) },
        { label: 'Increase',       value: `+${meta.increase_pct ?? 0}%` },
      ];
    case 'merchant':
      if (meta.is_new_merchant) return [
        { label: 'Amount',         value: fmt(meta.transaction_amount) },
        { label: 'Status',         value: 'First ever transaction' },
        { label: 'Category',       value: meta.category || '—' },
      ];
      return [
        { label: 'Typical Amount', value: fmt(meta.historical_mean) },
        { label: 'This Month',     value: fmt(meta.transaction_amount) },
        { label: 'Increase',       value: `+${meta.increase_pct ?? 0}%` },
      ];
    case 'subscription':
      return [
        { label: 'Monthly Cost',    value: fmt(meta.monthly_cost) },
        { label: 'Annual Cost',     value: fmt(meta.annual_cost) },
        { label: 'Months Detected', value: String(meta.occurrence_count ?? 0) },
      ];
    case 'budget':
      return [
        { label: 'Budget Limit',   value: fmt(meta.budget) },
        { label: 'Current Spend',  value: fmt(meta.current_spend) },
        { label: 'Projected',      value: fmt(meta.projected_spend) },
      ];
    default:
      return [];
  }
}

function getRecommendation(type, meta) {
  switch (type) {
    case 'transaction':
      return 'Review this transaction to confirm it was authorized and check for billing errors.';
    case 'category': {
      const cat = meta?.category || 'this category';
      const pct = meta?.increase_pct ?? 0;
      if (pct > 100)
        return `Your ${cat} spending has more than doubled. Consider setting or tightening a budget.`;
      return `Review recent ${cat} purchases and identify which are non-essential.`;
    }
    case 'merchant':
      if (meta?.is_new_merchant)
        return 'Verify you authorized this payment. If unrecognized, contact your bank immediately.';
      return 'Check if a subscription renewed, a price increased, or a duplicate charge occurred.';
    case 'subscription': {
      const annual = meta?.annual_cost ?? 0;
      return `This subscription costs ${fmt(annual)}/year. Evaluate if you're actively using it and whether it's worth keeping.`;
    }
    case 'budget':
      return 'Reduce discretionary spending in this category for the rest of the month to stay within budget.';
    default:
      return 'Review this item carefully.';
  }
}

// ── Skeleton ─────────────────────────────────────────────────────────────────

function SkeletonCard() {
  return (
    <div className="an-skeleton-card">
      <div className="an-sk an-sk--header" />
      <div className="an-sk an-sk--title" />
      <div className="an-sk an-sk--chips" />
      <div className="an-sk an-sk--body" />
    </div>
  );
}

// ── Anomaly Card ──────────────────────────────────────────────────────────────

function AnomalyCard({ anomaly }) {
  const typeMeta = TYPE_META[anomaly.type] || TYPE_META.transaction;
  const sevMeta  = SEV_META[anomaly.severity] || SEV_META.low;
  const stats    = getCardStats(anomaly.type, anomaly.meta_data);
  const rec      = getRecommendation(anomaly.type, anomaly.meta_data);

  return (
    <div
      className="anom-card"
      style={{ borderLeftColor: BORDER_COLOR[anomaly.severity], borderLeftWidth: '3px' }}
    >
      <div className="anom-card-header">
        <div className="anom-type-badge">
          <typeMeta.Icon size={13} color={typeMeta.color} />
          <span style={{ color: typeMeta.color }}>{typeMeta.label}</span>
        </div>
        <div
          className="anom-sev-badge"
          style={{ background: sevMeta.bg, color: sevMeta.color }}
        >
          {sevMeta.label} · {anomaly.score.toFixed(0)}
        </div>
      </div>

      <h3 className="anom-title">{anomaly.title}</h3>

      {stats.length > 0 && (
        <div className="anom-stats">
          {stats.map((s) => (
            <div className="anom-stat" key={s.label}>
              <span className="anom-stat-val">{s.value}</span>
              <span className="anom-stat-lbl">{s.label}</span>
            </div>
          ))}
        </div>
      )}

      <p className="anom-desc">{anomaly.description}</p>

      <div className="anom-rec">
        <Lightbulb size={13} />
        <span>{rec}</span>
      </div>

      <div className="anom-footer">
        <Calendar size={12} />
        <span>{timeAgo(anomaly.created_at)}</span>
      </div>
    </div>
  );
}

// ── Severity Chart ────────────────────────────────────────────────────────────

function SeverityChart({ stats }) {
  const data = ['critical', 'high', 'medium', 'low']
    .map((s) => ({
      name: SEV_META[s].label,
      count: stats?.by_severity?.[s] ?? 0,
      fill: SEV_META[s].bar,
    }))
    .filter((d) => d.count > 0);

  if (!data.length) return <p className="anom-empty-sub">No data</p>;

  return (
    <ResponsiveContainer width="100%" height={160}>
      <BarChart data={data} barSize={32} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <XAxis dataKey="name" tick={{ fontSize: 12, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fontSize: 11, fill: 'var(--text-muted)' }} axisLine={false} tickLine={false} allowDecimals={false} />
        <Tooltip
          formatter={(v) => [v, 'Anomalies']}
          contentStyle={{ fontSize: 12, borderRadius: 6, border: '1px solid var(--border)' }}
        />
        <Bar dataKey="count" radius={[4, 4, 0, 0]}>
          {data.map((d) => (
            <Cell key={d.name} fill={d.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// ── Subscriptions Table ───────────────────────────────────────────────────────

function SubscriptionsTable({ data }) {
  if (!data || data.subscriptions.length === 0) {
    return (
      <p className="anom-empty-sub">
        No recurring subscriptions detected in your transaction history.
      </p>
    );
  }

  return (
    <div className="sub-table-wrap">
      <table className="sub-table">
        <thead>
          <tr>
            <th>Merchant</th>
            <th>Category</th>
            <th>Months</th>
            <th>Monthly</th>
            <th>Annual</th>
          </tr>
        </thead>
        <tbody>
          {data.subscriptions.map((s) => (
            <tr key={s.anomaly_id}>
              <td className="sub-merchant">{s.merchant}</td>
              <td className="sub-cat">{s.category || '—'}</td>
              <td>{s.occurrence_count}</td>
              <td>{fmt(s.monthly_cost)}</td>
              <td className="sub-annual">{fmt(s.annual_cost)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="sub-total-row">
        <span>Total recurring cost</span>
        <span>
          <strong>{fmt(data.total_monthly_cost)}/mo</strong>
          &nbsp;·&nbsp;
          <strong>{fmt(data.total_annual_cost)}/yr</strong>
        </span>
      </div>
    </div>
  );
}

// ── Empty State ───────────────────────────────────────────────────────────────

function EmptyState({ onRun, running }) {
  return (
    <div className="anom-empty-state">
      <div className="anom-empty-icon">
        <ShieldCheck size={40} strokeWidth={1.5} />
      </div>
      <h2>Your spending behavior appears normal</h2>
      <p>
        No unusual patterns detected. FinMate analyzes transaction outliers,
        category spikes, new merchants, subscriptions, and budget risks.
      </p>
      <button
        className="anom-run-btn anom-run-btn--outline"
        onClick={onRun}
        disabled={running}
      >
        {running ? (
          <><RotateCcw size={14} className="spin" /> Analyzing…</>
        ) : (
          <><RotateCcw size={14} /> Run Analysis</>
        )}
      </button>
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function AnomaliesPage() {
  const [anomalies, setAnomalies]   = useState([]);
  const [summary, setSummary]       = useState(null);
  const [stats, setStats]           = useState(null);
  const [subs, setSubs]             = useState(null);
  const [loading, setLoading]       = useState(true);
  const [running, setRunning]       = useState(false);
  const [error, setError]           = useState('');
  const [filter, setFilter]         = useState('all');

  const loadAll = useCallback(async () => {
    setError('');
    try {
      const [a, su, st, sb] = await Promise.all([
        getAnomalies(),
        getAnomalySummary(),
        getAnomalyStats(),
        getSubscriptions(),
      ]);
      setAnomalies(a);
      setSummary(su);
      setStats(st);
      setSubs(sb);
    } catch {
      setError('Failed to load anomaly data. Please refresh.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadAll(); }, [loadAll]);

  const handleRun = async () => {
    setRunning(true);
    try {
      await runAnomalyDetection();
      await loadAll();
    } catch {
      setError('Analysis failed. Please try again.');
    } finally {
      setRunning(false);
    }
  };

  const filtered = filter === 'all'
    ? anomalies
    : anomalies.filter((a) => a.severity === filter);

  const subsCount = anomalies.filter((a) => a.type === 'subscription').length;

  return (
    <>
      <Topbar title="Anomalies" />
      <div className="anom-content">

        {/* Header row */}
        <div className="anom-header">
          <div>
            <h1 className="anom-page-title">Financial Anomalies</h1>
            <p className="anom-page-sub">
              Proactive detection of unusual patterns, risks, and recurring charges.
            </p>
          </div>
          <button
            className={`anom-run-btn${running ? ' anom-run-btn--loading' : ''}`}
            onClick={handleRun}
            disabled={running || loading}
          >
            {running ? (
              <><RotateCcw size={14} className="spin" /> Analyzing…</>
            ) : (
              <><RotateCcw size={14} /> Re-run Analysis</>
            )}
          </button>
        </div>

        {error && <div className="anom-error">{error}</div>}

        {/* Stats row */}
        <div className="anom-stats-grid">
          <StatsCard
            title="Total Alerts"
            value={loading ? '—' : String(summary?.total ?? 0)}
            trend="detected anomalies"
            trendColor="yellow"
            icon="budget"
          />
          <StatsCard
            title="Critical"
            value={loading ? '—' : String(summary?.critical ?? 0)}
            trend="requires immediate attention"
            trendColor="red"
            icon="spending"
          />
          <StatsCard
            title="High Risk"
            value={loading ? '—' : String(summary?.high ?? 0)}
            trend="review recommended"
            trendColor="red"
            icon="transactions"
          />
          <StatsCard
            title="Subscriptions"
            value={loading ? '—' : String(subsCount)}
            trend="recurring charges found"
            trendColor="blue"
            icon="savings"
          />
        </div>

        {/* Empty state */}
        {!loading && anomalies.length === 0 && (
          <EmptyState onRun={handleRun} running={running} />
        )}

        {/* Charts row */}
        {!loading && anomalies.length > 0 && (
          <div className="anom-charts-row">
            <div className="anom-card">
              <div className="anom-card-title">Severity Distribution</div>
              <SeverityChart stats={stats} />
            </div>
            <div className="anom-card">
              <div className="anom-card-title">By Type</div>
              <div className="anom-type-list">
                {(stats?.by_type ?? []).map((t) => {
                  const tm = TYPE_META[t.type] || { label: t.type, color: '#6b7280', Icon: AlertTriangle };
                  return (
                    <div className="anom-type-row" key={t.type}>
                      <div className="anom-type-name">
                        <tm.Icon size={14} color={tm.color} />
                        <span>{tm.label}</span>
                      </div>
                      <div className="anom-type-bar-wrap">
                        <div
                          className="anom-type-bar"
                          style={{
                            width: `${Math.round((t.count / (stats?.total || 1)) * 100)}%`,
                            background: tm.color,
                          }}
                        />
                      </div>
                      <span className="anom-type-count">{t.count}</span>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* Anomaly feed */}
        {!loading && anomalies.length > 0 && (
          <div className="anom-feed-section">
            <div className="anom-feed-header">
              <h2 className="anom-section-title">Alert Feed</h2>
              <div className="anom-filter-tabs">
                {['all', 'critical', 'high', 'medium', 'low'].map((s) => (
                  <button
                    key={s}
                    className={`anom-tab${filter === s ? ' anom-tab--active' : ''}`}
                    onClick={() => setFilter(s)}
                  >
                    {s === 'all' ? 'All' : SEV_META[s].label}
                    {s !== 'all' && summary?.[s] > 0 && (
                      <span className="anom-tab-count">{summary[s]}</span>
                    )}
                  </button>
                ))}
              </div>
            </div>

            {filtered.length === 0 ? (
              <p className="anom-empty-sub">No {filter} alerts.</p>
            ) : (
              <div className="anom-feed">
                {loading
                  ? Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)
                  : filtered.map((a) => <AnomalyCard key={a.id} anomaly={a} />)
                }
              </div>
            )}
          </div>
        )}

        {/* Subscriptions */}
        {!loading && (
          <div className="anom-card anom-subs-section">
            <div className="anom-card-title-row">
              <div>
                <div className="anom-card-title">Detected Subscriptions</div>
                <div className="anom-card-sub">
                  Recurring charges identified by consistent payment patterns
                </div>
              </div>
              {subs && subs.count > 0 && (
                <div className="anom-subs-total">
                  <span className="anom-subs-total-lbl">Monthly total</span>
                  <span className="anom-subs-total-val">{fmt(subs.total_monthly_cost)}</span>
                </div>
              )}
            </div>
            <SubscriptionsTable data={subs} />
          </div>
        )}

      </div>
    </>
  );
}
