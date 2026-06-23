import { useState, useEffect } from 'react';
import Topbar from './components/Topbar';
import HeroSection from './components/HeroSection';
import HealthScoreCard from './components/HealthScoreCard';
import AIInsights from './components/AIInsights';
import AlertsBanner from './components/AlertsBanner';
import BudgetProgress from './components/BudgetProgress';
import SpendingChart from './components/SpendingChart';
import { getDashboardOverview } from '../../services/analyticsService';
import { useSettings } from '../../context/SettingsContext';
import { formatCurrency } from '../../utils/format';
import './Dashboard.css';

function buildBriefing(healthScore, overview, forecast, anomalies, categories, currency) {
  const fmt = (v) => formatCurrency(v, currency);
  const items = [];

  const urgent = anomalies.find((a) => a.severity === 'critical') || anomalies.find((a) => a.severity === 'high');
  if (urgent) {
    items.push({
      type: 'risk',
      label: 'Biggest Risk',
      title: urgent.title,
      body: urgent.description,
    });
  }

  const atRisk = (forecast?.forecasts || []).filter((f) => f.risk === 'exceeded' || f.risk === 'high');
  if (atRisk.length > 0) {
    const worst = atRisk.reduce((a, b) =>
      b.projected_spend / b.budget > a.projected_spend / a.budget ? b : a
    );
    const projPct = Math.round((worst.projected_spend / worst.budget) * 100);
    items.push({
      type: 'warning',
      label: 'Budget Warning',
      title: `${worst.category} projected at ${projPct}% of budget`,
      body: `On track to spend ${fmt(worst.projected_spend)} vs ${fmt(worst.budget)} limit — ${fmt(worst.expected_overrun)} overrun expected with ${worst.days_remaining} days remaining.`,
    });
  }

  if (healthScore?.breakdown) {
    const b = healthScore.breakdown;
    const factors = [
      { name: 'Savings Rate', pct: b.savings_rate / b.savings_rate_max, score: b.savings_rate, max: b.savings_rate_max },
      { name: 'Expense Stability', pct: b.expense_stability / b.expense_stability_max, score: b.expense_stability, max: b.expense_stability_max },
      { name: 'Income Consistency', pct: b.income_consistency / b.income_consistency_max, score: b.income_consistency, max: b.income_consistency_max },
      { name: 'Diversification', pct: b.diversification / b.diversification_max, score: b.diversification, max: b.diversification_max },
    ];
    const weakest = factors.reduce((a, c) => (c.pct < a.pct ? c : a));
    const firstInsight = healthScore.insights?.[0] || 'Improving this factor has the highest impact on your financial health score.';
    items.push({
      type: 'info',
      label: 'Score Driver',
      title: `${weakest.name} is your weakest factor`,
      body: `${weakest.score.toFixed(0)} of ${weakest.max} pts (${Math.round(weakest.pct * 100)}%). ${firstInsight}`,
    });
  }

  const topCat = categories?.data?.[0];
  if (topCat && topCat.percentage > 25) {
    const potential = topCat.amount * 0.15;
    items.push({
      type: 'opportunity',
      label: 'Savings Opportunity',
      title: `${topCat.category} is ${topCat.percentage.toFixed(0)}% of total spending`,
      body: `${fmt(topCat.amount)} across ${topCat.count} transactions. A 15% reduction frees ${fmt(potential)}.`,
    });
  }

  if (overview) {
    const rate = overview.savings_rate;
    if (rate < 10) {
      items.push({
        type: 'warning',
        label: 'Savings Alert',
        title: `Savings rate ${rate.toFixed(0)}% — below the 20% target`,
        body: `Saving ${fmt(overview.savings)} of ${fmt(overview.income)} income. Reaching 20% means targeting ${fmt(overview.income * 0.2)} monthly.`,
      });
    } else if (rate >= 20) {
      items.push({
        type: 'success',
        label: 'Savings Performance',
        title: `Savings rate ${rate.toFixed(0)}% — exceeding target`,
        body: `${fmt(overview.savings)} saved of ${fmt(overview.income)} income. You're ahead of the 20% benchmark.`,
      });
    } else {
      items.push({
        type: 'info',
        label: 'Savings Recommendation',
        title: `Savings rate ${rate.toFixed(0)}% — room to grow`,
        body: `Saving ${fmt(overview.savings)} of ${fmt(overview.income)}. You're ${(20 - rate).toFixed(0)}% away from the recommended 20% target.`,
      });
    }
  }

  return items.slice(0, 5);
}

export default function Dashboard() {
  const { currency } = useSettings() || {};
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboardOverview()
      .then(({ health_score, overview, forecast, anomalies, categories, monthly_trend, top_merchants }) => {
        setData({
          healthScore: health_score,
          overview,
          forecast,
          anomalies,
          categories,
          trend: monthly_trend,
          merchants: top_merchants,
        });
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const briefingItems = data
    ? buildBriefing(data.healthScore, data.overview, data.forecast, data.anomalies, data.categories, currency)
    : [];

  const budgetRiskCount = data
    ? (data.forecast?.forecasts || []).filter((f) => f.risk === 'high' || f.risk === 'exceeded').length
    : 0;

  const criticalCount = data
    ? (data.anomalies || []).filter((a) => a.severity === 'critical').length
    : 0;

  return (
    <>
      <Topbar title="Financial Intelligence" />
      <div className="dashboard-content">

        <HeroSection
          loading={loading}
          healthScore={data?.healthScore}
          overview={data?.overview}
          budgetRiskCount={budgetRiskCount}
          criticalCount={criticalCount}
          anomalyCount={(data?.anomalies || []).length}
        />

        <div className="dashboard-mid-grid">
          <HealthScoreCard loading={loading} healthScore={data?.healthScore} />
          <AIInsights loading={loading} items={briefingItems} />
        </div>

        <AlertsBanner
          loading={loading}
          anomalies={data?.anomalies || []}
        />

        <div className="dashboard-bottom-grid">
          <BudgetProgress loading={loading} forecast={data?.forecast} />
          <SpendingChart
            loading={loading}
            trend={data?.trend}
            categories={data?.categories}
            overview={data?.overview}
          />
        </div>

      </div>
    </>
  );
}
