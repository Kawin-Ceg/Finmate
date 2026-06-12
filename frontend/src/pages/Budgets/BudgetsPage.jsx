import { useState, useEffect, useCallback } from 'react';
import { Plus, PiggyBank } from 'lucide-react';
import Topbar from '../Dashboard/components/Topbar';
import StatsCard from '../Dashboard/components/StatsCard';
import BudgetCard from './components/BudgetCard';
import BudgetForecast from './components/BudgetForecast';
import BudgetAlerts from './components/BudgetAlerts';
import CreateBudgetModal from './components/CreateBudgetModal';
import {
  getBudgets,
  getBudgetOverview,
  getBudgetForecast,
} from '../../services/budgetService';
import './BudgetsPage.css';

function formatINR(v) {
  if (v === null || v === undefined) return '₹—';
  return `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
}

export default function BudgetsPage() {
  const [budgets, setBudgets] = useState([]);
  const [overview, setOverview] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editBudget, setEditBudget] = useState(null);

  const loadData = useCallback(async () => {
    setError('');
    try {
      const [b, o, f] = await Promise.all([
        getBudgets(),
        getBudgetOverview(),
        getBudgetForecast(),
      ]);
      setBudgets(b);
      setOverview(o);
      setForecast(f);
    } catch {
      setError('Failed to load budgets. Please refresh.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleCreated = () => {
    setShowModal(false);
    setEditBudget(null);
    loadData();
  };

  const handleEdit = (budget) => {
    setEditBudget(budget);
    setShowModal(true);
  };

  const handleClose = () => {
    setShowModal(false);
    setEditBudget(null);
  };

  const trendColor = overview
    ? overview.remaining >= 0 ? 'green' : 'red'
    : 'blue';

  return (
    <>
      <Topbar title="Budgets" />
      <div className="dashboard-content">

        {/* ── Overview stats ── */}
        <div className="stats-grid">
          <StatsCard
            title="Total Budget"
            value={loading ? '—' : formatINR(overview?.total_budget)}
            trend="Monthly allocation"
            trendColor="blue"
            icon="budget"
          />
          <StatsCard
            title="Total Spent"
            value={loading ? '—' : formatINR(overview?.total_spent)}
            trend="Current month"
            trendColor={
              overview && overview.total_spent > overview.total_budget ? 'red' : 'yellow'
            }
            icon="spending"
          />
          <StatsCard
            title="Remaining"
            value={loading ? '—' : formatINR(overview?.remaining)}
            trend="Available to spend"
            trendColor={trendColor}
            icon="savings"
          />
          <StatsCard
            title="At Risk"
            value={loading ? '—' : String(overview?.at_risk_count ?? 0)}
            trend="categories above 85%"
            trendColor={
              overview && overview.at_risk_count > 0 ? 'red' : 'green'
            }
            icon="transactions"
          />
        </div>

        {/* ── Alerts (only when present) ── */}
        {!loading && forecast?.alerts?.length > 0 && (
          <BudgetAlerts alerts={forecast.alerts} />
        )}

        {/* ── Budget cards ── */}
        <div className="bpage-section">
          <div className="bpage-section-head">
            <div>
              <h2 className="bpage-section-title">Your Budgets</h2>
              <p className="bpage-section-sub">
                Monthly spending limits tracked against real transactions
              </p>
            </div>
            <button className="bpage-add-btn" onClick={() => setShowModal(true)}>
              <Plus size={14} strokeWidth={2.5} />
              Add Budget
            </button>
          </div>

          {error && <p className="bpage-error">{error}</p>}

          {loading ? (
            <div className="bpage-cards-grid">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="bc-skeleton" />
              ))}
            </div>
          ) : budgets.length === 0 ? (
            <div className="bpage-empty">
              <div className="bpage-empty-icon">
                <PiggyBank size={28} strokeWidth={1.5} />
              </div>
              <h3 className="bpage-empty-title">No budgets yet</h3>
              <p className="bpage-empty-sub">
                Create your first budget to start tracking spending against monthly limits.
              </p>
              <button className="bpage-add-btn" onClick={() => setShowModal(true)}>
                <Plus size={14} strokeWidth={2.5} />
                Create Budget
              </button>
            </div>
          ) : (
            <div className="bpage-cards-grid">
              {budgets.map((b) => (
                <BudgetCard
                  key={b.id}
                  budget={b}
                  onEdit={handleEdit}
                  onDeleted={loadData}
                />
              ))}
            </div>
          )}
        </div>

        {/* ── Forecast (only when budgets exist) ── */}
        {!loading && forecast?.forecasts?.length > 0 && (
          <BudgetForecast forecast={forecast} />
        )}

      </div>

      {showModal && (
        <CreateBudgetModal
          editBudget={editBudget}
          existingCategories={budgets.map((b) => b.category)}
          onCreated={handleCreated}
          onClose={handleClose}
        />
      )}
    </>
  );
}
