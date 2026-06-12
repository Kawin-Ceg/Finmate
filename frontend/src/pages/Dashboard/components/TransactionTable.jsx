import { Upload } from 'lucide-react';
import './TransactionTable.css';

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

export default function TransactionTable({ transactions = [], loading = false, onUploadClick }) {
  return (
    <div className="txn-card">
      <div className="txn-header">
        <div>
          <h2 className="txn-title">Recent Transactions</h2>
          <p className="txn-subtitle">
            {loading
              ? 'Loading...'
              : transactions.length > 0
              ? `Last ${transactions.length} transaction${transactions.length !== 1 ? 's' : ''}`
              : 'No transactions imported yet'}
          </p>
        </div>
      </div>

      <div className="txn-table-wrap">
        {loading ? (
          <table className="txn-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Category</th>
                <th>Merchant</th>
                <th className="txn-col-right">Amount</th>
                <th className="txn-col-right">Type</th>
              </tr>
            </thead>
            <tbody>
              {Array.from({ length: 5 }).map((_, i) => (
                <tr key={i}>
                  <td><div className="txn-skeleton" style={{ width: 80 }} /></td>
                  <td><div className="txn-skeleton txn-skeleton--badge" /></td>
                  <td><div className="txn-skeleton" style={{ width: 160 }} /></td>
                  <td className="txn-col-right"><div className="txn-skeleton" style={{ width: 72, marginLeft: 'auto' }} /></td>
                  <td className="txn-col-right"><div className="txn-skeleton txn-skeleton--badge" style={{ marginLeft: 'auto' }} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : transactions.length === 0 ? (
          <div className="txn-empty">
            <p className="txn-empty-title">No transactions yet.</p>
            <p className="txn-empty-sub">
              Upload your first bank statement to start seeing data here.
            </p>
            {onUploadClick && (
              <button className="txn-empty-btn" onClick={onUploadClick}>
                <Upload size={13} strokeWidth={2} />
                <span>Go to Transactions</span>
              </button>
            )}
          </div>
        ) : (
          <table className="txn-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Category</th>
                <th>Merchant</th>
                <th className="txn-col-right">Amount</th>
                <th className="txn-col-right">Type</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((txn) => {
                const cat = CATEGORY_COLORS[txn.category] || CATEGORY_COLORS.Other;
                return (
                  <tr key={txn.id}>
                    <td className="txn-date">{formatDate(txn.date)}</td>
                    <td>
                      <span
                        className="txn-badge"
                        style={{ background: cat.bg, color: cat.color }}
                      >
                        {txn.category}
                      </span>
                    </td>
                    <td className="txn-desc">{txn.merchant}</td>
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
                        className={`txn-status ${
                          txn.transaction_type === 'credit'
                            ? 'txn-status--completed'
                            : 'txn-status--pending'
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
    </div>
  );
}
