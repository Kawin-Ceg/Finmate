import { useState, useEffect } from 'react';
import { Upload, Search } from 'lucide-react';
import Topbar from '../Dashboard/components/Topbar';
import StatsCard from '../Dashboard/components/StatsCard';
import UploadModal from './components/UploadModal/UploadModal';
import {
  getTransactions,
  getTransactionSummary,
  getCategories,
} from '../../services/transactionService';
import './Transactions.css';

const CATEGORY_COLORS = {
  Food: { bg: '#FEF3C7', color: '#92400E' },
  Transport: { bg: '#DBEAFE', color: '#1E40AF' },
  Shopping: { bg: '#F3E8FF', color: '#6B21A8' },
  Utilities: { bg: '#F0FDF4', color: '#166534' },
  Entertainment: { bg: '#FEE2E2', color: '#991B1B' },
  Health: { bg: '#ECFDF5', color: '#065F46' },
  Income: { bg: '#DCFCE7', color: '#15803D' },
  Cash: { bg: '#FFF7ED', color: '#9A3412' },
  Transfers: { bg: '#EFF6FF', color: '#1D4ED8' },
  Insurance: { bg: '#FDF4FF', color: '#7E22CE' },
  Investment: { bg: '#F0FDF4', color: '#166534' },
  Education: { bg: '#FFFBEB', color: '#92400E' },
  Rent: { bg: '#FEF2F2', color: '#991B1B' },
  Subscriptions: { bg: '#F5F3FF', color: '#5B21B6' },
  Other: { bg: '#F1F5F9', color: '#475569' },
};

const MONTHS = [
  { value: 1, label: 'January' },
  { value: 2, label: 'February' },
  { value: 3, label: 'March' },
  { value: 4, label: 'April' },
  { value: 5, label: 'May' },
  { value: 6, label: 'June' },
  { value: 7, label: 'July' },
  { value: 8, label: 'August' },
  { value: 9, label: 'September' },
  { value: 10, label: 'October' },
  { value: 11, label: 'November' },
  { value: 12, label: 'December' },
];

function formatDate(dateStr) {
  return new Date(dateStr + 'T00:00:00').toLocaleDateString('en-IN', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

function formatAmount(amount, type) {
  const formatted = Number(amount).toLocaleString('en-IN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 2,
  });
  return type === 'credit' ? `+₹${formatted}` : `-₹${formatted}`;
}

function formatINR(value) {
  if (value === null || value === undefined) return '₹—';
  return `₹${Number(value).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
}

export default function Transactions() {
  const [summary, setSummary] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [categories, setCategories] = useState([]);
  const [summaryLoading, setSummaryLoading] = useState(true);
  const [loading, setLoading] = useState(true);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('');
  const [month, setMonth] = useState('');
  const [year, setYear] = useState('');
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const t = setTimeout(() => setSearch(searchInput), 350);
    return () => clearTimeout(t);
  }, [searchInput]);

  useEffect(() => {
    setPage(1);
  }, [search, category, month, year]);

  useEffect(() => {
    setSummaryLoading(true);
    getTransactionSummary()
      .then(setSummary)
      .catch(console.error)
      .finally(() => setSummaryLoading(false));
    getCategories().then(setCategories).catch(console.error);
  }, [refreshKey]);

  useEffect(() => {
    setLoading(true);
    const params = { page, limit: 20 };
    if (search) params.search = search;
    if (category) params.category = category;
    if (month) params.month = parseInt(month);
    if (year) params.year = parseInt(year);

    getTransactions(params)
      .then((data) => {
        setTransactions(data.transactions);
        setTotalPages(data.total_pages);
        setTotal(data.total);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [page, search, category, month, year, refreshKey]);

  const handleUploadSuccess = () => {
    setRefreshKey((k) => k + 1);
    setPage(1);
    setUploadOpen(false);
  };

  const hasFilters = search || category || month || year;
  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);

  return (
    <>
      <Topbar title="Transactions" />
      <div className="dashboard-content">

        <div className="txnp-header">
          <div>
            <h1 className="txnp-heading">Transactions</h1>
            <p className="txnp-subheading">Upload and analyze your financial activity.</p>
          </div>
          <button className="txnp-upload-btn" onClick={() => setUploadOpen(true)}>
            <Upload size={14} strokeWidth={2} />
            <span>Upload Statement</span>
          </button>
        </div>

        <div className="stats-grid">
          <StatsCard
            title="Total Spending"
            value={summaryLoading ? '—' : formatINR(summary?.total_spending)}
            trend={summaryLoading ? '' : `across all transactions`}
            trendColor="red"
            icon="spending"
          />
          <StatsCard
            title="Total Income"
            value={summaryLoading ? '—' : formatINR(summary?.total_income)}
            trend={summaryLoading ? '' : 'credited'}
            trendColor="blue"
            icon="savings"
          />
          <StatsCard
            title="Top Category"
            value={summaryLoading ? '—' : (summary?.top_category ?? 'None')}
            trend={summaryLoading ? '' : 'highest spend'}
            trendColor="yellow"
            icon="budget"
          />
          <StatsCard
            title="Transactions"
            value={summaryLoading ? '—' : String(summary?.total_transactions ?? 0)}
            trend={summaryLoading ? '' : 'total records'}
            trendColor="blue"
            icon="transactions"
          />
        </div>

        <div className="txn-card">
          <div className="txnp-filters">
            <div className="txnp-search-wrap">
              <Search size={13} className="txnp-search-icon" />
              <input
                type="text"
                placeholder="Search merchant or category..."
                className="txnp-search-input"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
              />
            </div>
            <div className="txnp-select-row">
              <select
                className="txnp-select"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
              >
                <option value="">All Categories</option>
                {categories.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
              <select
                className="txnp-select"
                value={month}
                onChange={(e) => setMonth(e.target.value)}
              >
                <option value="">All Months</option>
                {MONTHS.map((m) => (
                  <option key={m.value} value={m.value}>{m.label}</option>
                ))}
              </select>
              <select
                className="txnp-select"
                value={year}
                onChange={(e) => setYear(e.target.value)}
              >
                <option value="">All Years</option>
                {years.map((y) => (
                  <option key={y} value={y}>{y}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="txn-table-wrap">
            {loading ? (
              <table className="txn-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Merchant</th>
                    <th>Category</th>
                    <th className="txn-col-right">Amount</th>
                    <th className="txn-col-right">Type</th>
                  </tr>
                </thead>
                <tbody>
                  {Array.from({ length: 7 }).map((_, i) => (
                    <tr key={i}>
                      <td><div className="skeleton" style={{ width: 80, height: 14 }} /></td>
                      <td><div className="skeleton" style={{ width: 140, height: 14 }} /></td>
                      <td><div className="skeleton" style={{ width: 70, height: 22, borderRadius: 99 }} /></td>
                      <td className="txn-col-right"><div className="skeleton" style={{ width: 72, height: 14, marginLeft: 'auto' }} /></td>
                      <td className="txn-col-right"><div className="skeleton" style={{ width: 50, height: 22, borderRadius: 99, marginLeft: 'auto' }} /></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : transactions.length === 0 ? (
              <div className="txn-empty">
                {hasFilters ? (
                  <>
                    <p className="txn-empty-title">No transactions match your search.</p>
                    <p className="txn-empty-sub">Try adjusting your filters above.</p>
                  </>
                ) : (
                  <>
                    <p className="txn-empty-title">No transactions yet.</p>
                    <p className="txn-empty-sub">
                      Upload your first bank statement to begin generating insights.
                    </p>
                    <button className="txnp-upload-btn" onClick={() => setUploadOpen(true)}>
                      <Upload size={14} strokeWidth={2} />
                      <span>Upload Statement</span>
                    </button>
                  </>
                )}
              </div>
            ) : (
              <table className="txn-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Merchant</th>
                    <th>Category</th>
                    <th className="txn-col-right">Amount</th>
                    <th className="txn-col-right">Type</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((txn) => {
                    const catStyle = CATEGORY_COLORS[txn.category] || CATEGORY_COLORS.Other;
                    return (
                      <tr key={txn.id}>
                        <td className="txn-date">{formatDate(txn.date)}</td>
                        <td className="txn-desc">{txn.merchant}</td>
                        <td>
                          <div className="txn-cat-cell">
                            <span
                              className="txn-badge"
                              style={{ background: catStyle.bg, color: catStyle.color }}
                            >
                              {txn.category}
                            </span>
                            {txn.categorization_method === 'ml' &&
                              txn.prediction_confidence != null && (
                                <span
                                  className="txn-conf"
                                  title="ML confidence score"
                                >
                                  {Math.round(txn.prediction_confidence * 100)}%
                                </span>
                              )}
                          </div>
                        </td>
                        <td
                          className={`txn-amount txn-col-right ${
                            txn.transaction_type === 'credit'
                              ? 'txn-amount--positive'
                              : 'txn-amount--negative'
                          }`}
                        >
                          {formatAmount(txn.amount, txn.transaction_type)}
                        </td>
                        <td className="txn-col-right">
                          <span
                            className={`txn-status txn-status--${
                              txn.transaction_type === 'credit' ? 'credit' : 'debit'
                            }`}
                          >
                            {txn.transaction_type === 'credit' ? 'Credit' : 'Debit'}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>

          {!loading && total > 0 && (
            <div className="txnp-pagination">
              <span className="txnp-pagination-info">
                {total.toLocaleString('en-IN')} transaction{total !== 1 ? 's' : ''}
              </span>
              <div className="txnp-pagination-controls">
                <button
                  className="txnp-page-btn"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  Previous
                </button>
                <span className="txnp-page-indicator">
                  Page {page} of {totalPages}
                </span>
                <button
                  className="txnp-page-btn"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>

      </div>

      <UploadModal
        isOpen={uploadOpen}
        onClose={() => setUploadOpen(false)}
        onSuccess={handleUploadSuccess}
      />
    </>
  );
}
