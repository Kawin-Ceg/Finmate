import { Lightbulb } from 'lucide-react';

export default function HealthInsights({ insights, loading }) {
  return (
    <div className="an-card">
      <div className="an-card-header">
        <div>
          <h2 className="an-card-title">Financial Insights</h2>
          <p className="an-card-sub">Personalised observations from your data</p>
        </div>
      </div>
      <div className="an-card-body">
        {loading ? (
          <div className="an-chart-skeleton" style={{ height: 140 }} />
        ) : !insights || insights.length === 0 ? (
          <div className="an-chart-empty" style={{ height: 140 }}>
            Upload transactions to generate insights
          </div>
        ) : (
          <div className="insight-list">
            {insights.map((text, i) => (
              <div key={i} className="insight-item">
                <div className="insight-icon">
                  <Lightbulb size={13} strokeWidth={1.75} />
                </div>
                <p className="insight-text">{text}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
