export default function SpendingHeatmap({ data, loading }) {
  const maxAvg = data.length > 0 ? Math.max(...data.map(d => d.average_spending), 1) : 1;
  const hasData = data.some(d => d.average_spending > 0);

  function fmtAvg(v) {
    if (v <= 0) return '—';
    if (v >= 100000) return `₹${(v / 100000).toFixed(1)}L`;
    if (v >= 1000) return `₹${(v / 1000).toFixed(1)}k`;
    return `₹${v.toFixed(0)}`;
  }

  return (
    <div className="an-card">
      <div className="an-card-header">
        <div>
          <h2 className="an-card-title">Spending Heatmap</h2>
          <p className="an-card-sub">Average spend by day of week</p>
        </div>
      </div>
      <div className="an-card-body">
        {loading ? (
          <div className="an-chart-skeleton" style={{ height: 140 }} />
        ) : !hasData ? (
          <div className="an-chart-empty" style={{ height: 140 }}>No spending data yet</div>
        ) : (
          <>
            <div className="heatmap-grid">
              {data.map((d) => {
                const intensity = d.average_spending / maxAvg;
                const alpha = 0.08 + intensity * 0.72;
                return (
                  <div key={d.day} className="heatmap-cell">
                    <div
                      className="heatmap-box"
                      style={{ background: `rgba(37, 99, 235, ${alpha})` }}
                      title={`${d.day}: avg ₹${d.average_spending.toLocaleString('en-IN')} (${d.transaction_count} txns)`}
                    />
                    <span className="heatmap-day">{d.day}</span>
                    <span className="heatmap-avg">{fmtAvg(d.average_spending)}</span>
                  </div>
                );
              })}
            </div>
            <p className="heatmap-note">Average transaction amount per day</p>
          </>
        )}
      </div>
    </div>
  );
}
