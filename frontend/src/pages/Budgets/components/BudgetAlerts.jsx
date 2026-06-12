import { AlertTriangle, TrendingUp, Info } from 'lucide-react';
import './BudgetAlerts.css';

function classifyAlert(text) {
  const t = text.toLowerCase();
  if (t.includes('exceeded')) return 'exceeded';
  if (t.includes('likely to exceed') || t.includes('exceed')) return 'warning';
  return 'info';
}

const ALERT_STYLES = {
  exceeded: {
    Icon: AlertTriangle,
    color: '#EF4444',
    bg: '#FEF2F2',
    border: '#FECACA',
    iconBg: '#FEE2E2',
  },
  warning: {
    Icon: TrendingUp,
    color: '#F97316',
    bg: '#FFF7ED',
    border: '#FED7AA',
    iconBg: '#FFEDD5',
  },
  info: {
    Icon: Info,
    color: '#F59E0B',
    bg: '#FFFBEB',
    border: '#FDE68A',
    iconBg: '#FEF3C7',
  },
};

export default function BudgetAlerts({ alerts }) {
  return (
    <div className="alerts-wrap">
      <div className="alerts-head">
        <span className="alerts-title">Budget Alerts</span>
        <span className="alerts-badge">{alerts.length}</span>
      </div>
      <div className="alerts-list">
        {alerts.map((alert, i) => {
          const type = classifyAlert(alert);
          const { Icon, color, bg, border, iconBg } = ALERT_STYLES[type];
          return (
            <div
              key={i}
              className="alert-item"
              style={{ background: bg, borderColor: border }}
            >
              <div className="alert-icon" style={{ background: iconBg }}>
                <Icon size={13} style={{ color }} strokeWidth={2} />
              </div>
              <span className="alert-text">{alert}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
