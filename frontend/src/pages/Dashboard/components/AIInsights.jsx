import { TrendingUp, Calendar, CheckCircle, Smartphone } from 'lucide-react';
import './AIInsights.css';

const INSIGHTS = [
  {
    type: 'warning',
    icon: TrendingUp,
    title: 'Food delivery up 18%',
    description:
      'Your food delivery spending increased by 18% compared to last month. Consider cooking at home more often to meet your budget.',
  },
  {
    type: 'info',
    icon: Calendar,
    title: 'Weekend spending pattern',
    description:
      'Weekend expenses account for 42% of your discretionary spending. Most of this is concentrated on Saturday afternoons.',
  },
  {
    type: 'success',
    icon: CheckCircle,
    title: 'Transportation on track',
    description:
      'Your transportation spending is 38% below budget this month — ₹1,900 saved. Great discipline.',
  },
  {
    type: 'warning',
    icon: Smartphone,
    title: 'Review your subscriptions',
    description:
      '7 active subscriptions totalling ₹2,847/month detected. Removing unused ones could save ₹2,300 monthly.',
  },
];

export default function AIInsights() {
  return (
    <div className="insights-card">
      <div className="insights-header">
        <div className="insights-header-label">
          <span className="insights-badge">AI</span>
          <h2 className="insights-title">AI Insights</h2>
        </div>
        <p className="insights-subtitle">Personalized for June 2025</p>
      </div>

      <div className="insights-list">
        {INSIGHTS.map((item, i) => {
          const Icon = item.icon;
          return (
            <div key={i} className={`insight-item insight-item--${item.type}`}>
              <div className={`insight-icon insight-icon--${item.type}`}>
                <Icon size={14} strokeWidth={2} />
              </div>
              <div className="insight-body">
                <span className="insight-item-title">{item.title}</span>
                <p className="insight-desc">{item.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
