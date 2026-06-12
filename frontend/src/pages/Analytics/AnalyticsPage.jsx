import { useState, useEffect } from 'react';
import Topbar from '../Dashboard/components/Topbar';
import StatsCard from '../Dashboard/components/StatsCard';
import HealthScoreCard from './components/HealthScoreCard';
import MonthlyTrendChart from './components/MonthlyTrendChart';
import CategoryBreakdownChart from './components/CategoryBreakdownChart';
import CashflowChart from './components/CashflowChart';
import SpendingHeatmap from './components/SpendingHeatmap';
import TopMerchantsTable from './components/TopMerchantsTable';
import HealthInsights from './components/HealthInsights';
import {
  getOverview,
  getMonthlyTrend,
  getCategoryBreakdown,
  getTopMerchants,
  getCashflow,
  getHeatmap,
  getHealthScore,
} from '../../services/analyticsService';
import './AnalyticsPage.css';

function formatINR(value) {
  if (value === null || value === undefined) return '₹—';
  return `₹${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
}

export default function AnalyticsPage() {
  const [overview, setOverview] = useState(null);
  const [monthlyTrend, setMonthlyTrend] = useState([]);
  const [categoryBreakdown, setCategoryBreakdown] = useState([]);
  const [topMerchants, setTopMerchants] = useState([]);
  const [cashflow, setCashflow] = useState([]);
  const [heatmap, setHeatmap] = useState([]);
  const [healthScore, setHealthScore] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getOverview(),
      getMonthlyTrend(),
      getCategoryBreakdown(),
      getTopMerchants(),
      getCashflow(),
      getHeatmap(),
      getHealthScore(),
    ])
      .then(([ov, mt, cb, tm, cf, hm, hs]) => {
        setOverview(ov);
        setMonthlyTrend(mt.data);
        setCategoryBreakdown(cb.data);
        setTopMerchants(tm.data);
        setCashflow(cf.data);
        setHeatmap(hm.data);
        setHealthScore(hs);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const srColor =
    (overview?.savings_rate ?? 0) >= 20 ? 'green' :
    (overview?.savings_rate ?? 0) >= 10 ? 'yellow' : 'red';

  const netSavingsColor = (overview?.savings ?? 0) >= 0 ? 'green' : 'red';

  return (
    <>
      <Topbar title="Analytics" />
      <div className="analytics-content">

        {/* Row 1 — Health Score + Overview */}
        <div className="analytics-top-grid">
          <HealthScoreCard data={healthScore} loading={loading} />
          <div className="analytics-overview-grid">
            <StatsCard
              title="Total Income"
              value={loading ? '—' : formatINR(overview?.income)}
              trend="all uploaded statements"
              trendColor="green"
              icon="savings"
            />
            <StatsCard
              title="Total Expenses"
              value={loading ? '—' : formatINR(overview?.expense)}
              trend="across all categories"
              trendColor="red"
              icon="spending"
            />
            <StatsCard
              title="Net Savings"
              value={loading ? '—' : formatINR(overview?.savings)}
              trend="income minus expenses"
              trendColor={netSavingsColor}
              icon="savings"
            />
            <StatsCard
              title="Savings Rate"
              value={loading ? '—' : `${overview?.savings_rate ?? 0}%`}
              trend="of income retained"
              trendColor={srColor}
              icon="budget"
            />
          </div>
        </div>

        {/* Row 2 — Monthly Trend */}
        <MonthlyTrendChart data={monthlyTrend} loading={loading} />

        {/* Row 3 — Category Breakdown + Top Merchants */}
        <div className="analytics-mid-grid">
          <CategoryBreakdownChart data={categoryBreakdown} loading={loading} />
          <TopMerchantsTable data={topMerchants} loading={loading} />
        </div>

        {/* Row 4 — Cashflow */}
        <CashflowChart data={cashflow} loading={loading} />

        {/* Row 5 — Heatmap + Insights */}
        <div className="analytics-bottom-grid">
          <SpendingHeatmap data={heatmap} loading={loading} />
          <HealthInsights insights={healthScore?.insights} loading={loading} />
        </div>

      </div>
    </>
  );
}
