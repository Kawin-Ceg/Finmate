import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import Topbar from './components/Topbar';
import StatsCard from './components/StatsCard';
import TransactionTable from './components/TransactionTable';
import BudgetProgress from './components/BudgetProgress';
import AIInsights from './components/AIInsights';
import SpendingChart from './components/SpendingChart';
import { getTransactionSummary, getTransactions } from '../../services/transactionService';
import AlertsBanner from './components/AlertsBanner';
import './Dashboard.css';

function formatINR(value) {
  if (value === null || value === undefined) return '₹—';
  return `₹${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
}

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [recentTransactions, setRecentTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      getTransactionSummary(),
      getTransactions({ limit: 5 }),
    ])
      .then(([summaryData, txnData]) => {
        setSummary(summaryData);
        setRecentTransactions(txnData.transactions);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const savings =
    summary
      ? summary.total_income - summary.total_spending
      : null;

  return (
    <>
      <Topbar title="Dashboard" />
      <div className="dashboard-content">

        <AlertsBanner />

        <div className="stats-grid">
          <StatsCard
            title="Monthly Spending"
            value={loading ? '—' : formatINR(summary?.total_spending)}
            trend={loading ? '' : `${summary?.total_transactions ?? 0} transactions`}
            trendColor="red"
            icon="spending"
          />
          <StatsCard
            title="Net Savings"
            value={loading ? '—' : formatINR(savings)}
            trend={loading ? '' : 'income minus spending'}
            trendColor={savings !== null && savings >= 0 ? 'green' : 'red'}
            icon="savings"
          />
          <StatsCard
            title="Top Category"
            value={loading ? '—' : (summary?.top_category ?? 'None')}
            trend={loading ? '' : 'highest spending'}
            trendColor="yellow"
            icon="budget"
          />
          <StatsCard
            title="Transactions"
            value={loading ? '—' : String(summary?.total_transactions ?? 0)}
            trend={loading ? '' : 'total records'}
            trendColor="blue"
            icon="transactions"
          />
        </div>

        <div className="dashboard-mid-grid">
          <SpendingChart />
          <AIInsights />
        </div>

        <TransactionTable
          transactions={recentTransactions}
          loading={loading}
          onUploadClick={() => navigate('/dashboard/transactions')}
        />

        <BudgetProgress />

      </div>
    </>
  );
}
