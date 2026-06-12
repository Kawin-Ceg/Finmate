import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, ArrowRight } from 'lucide-react';
import { getAnomalySummary } from '../../../services/anomalyService';
import './AlertsBanner.css';

export default function AlertsBanner() {
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    getAnomalySummary()
      .then(setSummary)
      .catch(() => {});
  }, []);

  if (!summary || summary.total === 0) return null;

  const hasUrgent = summary.critical > 0 || summary.high > 0;

  return (
    <div className={`ab-banner${hasUrgent ? ' ab-banner--urgent' : ''}`}>
      <div className="ab-icon">
        <AlertTriangle size={15} />
      </div>

      <div className="ab-body">
        <span className="ab-headline">
          {summary.total} Financial Alert{summary.total !== 1 ? 's' : ''} Detected
        </span>
        <div className="ab-chips">
          {summary.critical > 0 && (
            <span className="ab-chip ab-chip--critical">{summary.critical} Critical</span>
          )}
          {summary.high > 0 && (
            <span className="ab-chip ab-chip--high">{summary.high} High</span>
          )}
          {summary.medium > 0 && (
            <span className="ab-chip ab-chip--medium">{summary.medium} Medium</span>
          )}
          {summary.low > 0 && (
            <span className="ab-chip ab-chip--low">{summary.low} Low</span>
          )}
        </div>
      </div>

      <Link to="/dashboard/anomalies" className="ab-cta">
        Review Alerts <ArrowRight size={13} />
      </Link>
    </div>
  );
}
