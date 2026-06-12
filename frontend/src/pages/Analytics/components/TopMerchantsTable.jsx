export default function TopMerchantsTable({ data, loading }) {
  return (
    <div className="an-card">
      <div className="an-card-header">
        <div>
          <h2 className="an-card-title">Top Merchants</h2>
          <p className="an-card-sub">Highest spend destinations</p>
        </div>
      </div>
      <div className="an-card-body">
        {loading ? (
          <div className="an-chart-skeleton" style={{ height: 220 }} />
        ) : data.length === 0 ? (
          <div className="an-chart-empty" style={{ height: 220 }}>No merchant data yet</div>
        ) : (
          <div className="merchant-list">
            {data.map((m, i) => (
              <div key={m.merchant} className="merchant-item">
                <span className="merchant-rank">{i + 1}</span>
                <div className="merchant-info">
                  <span className="merchant-name">{m.merchant}</span>
                  <span className="merchant-count">
                    {m.transaction_count} transaction{m.transaction_count !== 1 ? 's' : ''}
                  </span>
                </div>
                <span className="merchant-amount">
                  ₹{m.total_amount.toLocaleString('en-IN', { maximumFractionDigits: 0 })}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
