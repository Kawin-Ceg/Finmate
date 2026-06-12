import './BudgetForecast.css';

const MONTH_NAMES = [
  '', 'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

const RISK_COLORS = {
  safe:     '#10B981',
  watch:    '#F59E0B',
  high:     '#F97316',
  exceeded: '#EF4444',
};

const RISK_LABELS = {
  safe:     'On Track',
  watch:    'Watch',
  high:     'At Risk',
  exceeded: 'Exceeded',
};

function formatINR(v) {
  return `₹${Number(v).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`;
}

export default function BudgetForecast({ forecast }) {
  const { forecasts, month, year } = forecast;

  return (
    <div className="forecast-card">
      <div className="forecast-header">
        <div>
          <h3 className="forecast-title">Month-End Forecast</h3>
          <p className="forecast-sub">
            {MONTH_NAMES[month]} {year} — projected end-of-month spend based on current daily rate
          </p>
        </div>
      </div>

      <div className="forecast-table-wrap">
        <table className="forecast-table">
          <thead>
            <tr>
              <th>Category</th>
              <th className="ta-right">Budget</th>
              <th className="ta-right">Current</th>
              <th className="ta-right">Projected</th>
              <th className="ta-right">Overrun</th>
              <th className="ta-center">Status</th>
            </tr>
          </thead>
          <tbody>
            {forecasts.map((f) => (
              <tr key={f.category}>
                <td className="ft-cat">{f.category}</td>
                <td className="ta-right ft-num">{formatINR(f.budget)}</td>
                <td className="ta-right ft-num">{formatINR(f.current_spend)}</td>
                <td className={`ta-right ft-num${f.projected_spend > f.budget ? ' ft-over' : ''}`}>
                  {formatINR(f.projected_spend)}
                </td>
                <td className="ta-right ft-num">
                  {f.expected_overrun > 0
                    ? <span className="ft-overrun-val">{formatINR(f.expected_overrun)}</span>
                    : <span className="ft-ok">—</span>}
                </td>
                <td className="ta-center">
                  <span
                    className="ft-badge"
                    style={{ color: RISK_COLORS[f.risk] }}
                  >
                    {RISK_LABELS[f.risk] || f.risk}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="forecast-note">
        Projections use a daily spend rate. Actual results may vary based on irregular spending patterns.
      </p>
    </div>
  );
}
