import { Link } from 'react-router-dom';
import { Zap, ArrowRight } from 'lucide-react';
import './AlertsBanner.css';

const SEV_ORDER = { critical: 0, high: 1, medium: 2, low: 3 };

const TYPE_LABEL = {
  transaction:   'Transaction',
  category:      'Category Spike',
  merchant:      'Merchant',
  subscription:  'Subscription',
  budget_risk:   'Budget Risk',
};

function AnomalyCard({ anomaly }) {
  const sev = anomaly.severity;
  return (
    <div className={`ac-card ac-card--${sev}`}>
      <div className="ac-card-top">
        <span className={`ac-sev-badge ac-sev-badge--${sev}`}>{sev}</span>
        <span className="ac-type-label">{TYPE_LABEL[anomaly.type] || anomaly.type}</span>
        <span className="ac-score">Score {Math.round(anomaly.score)}</span>
      </div>
      <p className="ac-title">{anomaly.title}</p>
      <p className="ac-desc">{anomaly.description}</p>
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="ac-card ac-card--skeleton">
      <div className="ac-skel-top">
        <div className="ac-skel ac-skel--badge" />
        <div className="ac-skel ac-skel--tag" />
      </div>
      <div className="ac-skel ac-skel--title" />
      <div className="ac-skel ac-skel--desc" />
    </div>
  );
}

export default function AlertsBanner({ loading, anomalies = [] }) {
  const sorted = [...anomalies].sort(
    (a, b) => (SEV_ORDER[a.severity] ?? 99) - (SEV_ORDER[b.severity] ?? 99)
  );
  const visible = sorted.slice(0, 3);

  const critCount = anomalies.filter((a) => a.severity === 'critical').length;
  const highCount = anomalies.filter((a) => a.severity === 'high').length;
  const totalCount = anomalies.length;

  if (!loading && totalCount === 0) return null;

  return (
    <div className="ac-section">
      <div className="ac-section-header">
        <div className="ac-header-left">
          <Zap size={14} strokeWidth={2} className="ac-header-icon" />
          <div>
            <h2 className="ac-section-title">Anomaly Intelligence Center</h2>
            <p className="ac-section-sub">
              {loading ? 'Scanning transactions…' :
                `${totalCount} anomal${totalCount === 1 ? 'y' : 'ies'} detected · ${critCount} critical · ${highCount} high`}
            </p>
          </div>
        </div>
        <Link to="/dashboard/anomalies" className="ac-view-all">
          View all <ArrowRight size={12} />
        </Link>
      </div>

      <div className="ac-grid">
        {loading
          ? Array.from({ length: 3 }).map((_, i) => <SkeletonCard key={i} />)
          : visible.map((a) => <AnomalyCard key={a.id} anomaly={a} />)
        }
      </div>
    </div>
  );
}
