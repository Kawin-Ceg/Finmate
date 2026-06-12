import { CreditCard, DollarSign, Target, ArrowLeftRight } from 'lucide-react';
import './StatsCard.css';

const ICONS = {
  spending: CreditCard,
  savings: DollarSign,
  budget: Target,
  transactions: ArrowLeftRight,
};

export default function StatsCard({ title, value, trend, trendColor, icon }) {
  const Icon = ICONS[icon] || CreditCard;

  return (
    <div className={`stats-card stats-card--${trendColor}`}>
      <div className="stats-card-top">
        <span className="stats-card-title">{title}</span>
        <div className="stats-card-icon-wrap">
          <Icon size={15} strokeWidth={1.75} />
        </div>
      </div>
      <div className="stats-card-value">{value}</div>
      {trend && (
        <div className={`stats-card-trend stats-card-trend--${trendColor}`}>
          {trend}
        </div>
      )}
    </div>
  );
}
