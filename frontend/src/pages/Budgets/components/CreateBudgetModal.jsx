import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import { createBudget, updateBudget } from '../../../services/budgetService';
import './CreateBudgetModal.css';

const ALL_CATEGORIES = [
  'Food', 'Transport', 'Shopping', 'Entertainment', 'Utilities',
  'Bills', 'Health', 'Education', 'Rent', 'Insurance',
  'Investment', 'Subscriptions', 'Cash', 'Transfers', 'Other',
];

export default function CreateBudgetModal({
  editBudget,
  existingCategories,
  onCreated,
  onClose,
}) {
  const isEdit = !!editBudget;

  const [category, setCategory] = useState(editBudget?.category || '');
  const [limit, setLimit] = useState(
    editBudget ? String(editBudget.monthly_limit) : ''
  );
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const available = isEdit
    ? ALL_CATEGORIES
    : ALL_CATEGORIES.filter((c) => !existingCategories.includes(c));

  useEffect(() => {
    if (!isEdit && available.length > 0 && !category) {
      setCategory(available[0]);
    }
  }, [isEdit, available, category]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    const numLimit = parseFloat(limit);
    if (!category) {
      setError('Please select a category.');
      return;
    }
    if (!limit || isNaN(numLimit) || numLimit <= 0) {
      setError('Please enter a valid budget amount greater than 0.');
      return;
    }
    try {
      setLoading(true);
      if (isEdit) {
        await updateBudget(editBudget.id, { monthly_limit: numLimit });
      } else {
        await createBudget({ category, monthly_limit: numLimit });
      }
      onCreated();
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="cbm-box" onClick={(e) => e.stopPropagation()}>
        <div className="cbm-header">
          <div>
            <h3 className="cbm-title">
              {isEdit ? 'Edit Budget' : 'Create Budget'}
            </h3>
            <p className="cbm-subtitle">
              {isEdit
                ? `Update the monthly limit for ${editBudget.category}`
                : 'Set a monthly spending limit for a category'}
            </p>
          </div>
          <button className="cbm-close" onClick={onClose} aria-label="Close">
            <X size={15} strokeWidth={2} />
          </button>
        </div>

        <form className="cbm-form" onSubmit={handleSubmit}>
          <div className="cbm-field">
            <label className="cbm-label">Category</label>
            {isEdit ? (
              <div className="cbm-readonly">{editBudget.category}</div>
            ) : available.length === 0 ? (
              <div className="cbm-readonly cbm-readonly--muted">
                All categories already have budgets
              </div>
            ) : (
              <select
                className="cbm-select"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                required
              >
                {available.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            )}
          </div>

          <div className="cbm-field">
            <label className="cbm-label">Monthly Limit</label>
            <div className="cbm-amount-wrap">
              <span className="cbm-currency">₹</span>
              <input
                className="cbm-input"
                type="number"
                value={limit}
                onChange={(e) => setLimit(e.target.value)}
                placeholder="5000"
                min="1"
                step="100"
                required
                autoFocus={isEdit}
              />
            </div>
          </div>

          {error && <div className="cbm-error">{error}</div>}

          <div className="cbm-footer">
            <button type="button" className="cbm-cancel" onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              className="cbm-submit"
              disabled={loading || (!isEdit && available.length === 0)}
            >
              {loading
                ? isEdit ? 'Saving…' : 'Creating…'
                : isEdit ? 'Save Changes' : 'Create Budget'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
