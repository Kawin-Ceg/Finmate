import './Trust.css';

const PILLARS = [
  {
    icon: '🔒',
    title: 'No bank connection required',
    description:
      'FinMate works with exported statements. Your bank login credentials are never requested or stored.',
  },
  {
    icon: '🛡',
    title: 'Bank-level encryption',
    description:
      'All data is encrypted at rest and in transit using AES-256. Your financial data never travels unencrypted.',
  },
  {
    icon: '🚫',
    title: 'Zero data selling',
    description:
      'Your transaction data is never shared with advertisers, data brokers, or third parties. Period.',
  },
  {
    icon: '🇮🇳',
    title: 'Built for India',
    description:
      'Trained on Indian merchant names, INR amounts, and local spending patterns. Not a US product retrofitted.',
  },
];

export default function Trust() {
  return (
    <section className="trust" id="security">
      <div className="trust-inner">
        <div className="trust-header">
          <span className="section-eyebrow">Security &amp; privacy</span>
          <h2 className="trust-title">Your financial data deserves respect</h2>
          <p className="trust-sub">
            We built FinMate with privacy as a first principle, not an afterthought.
          </p>
        </div>

        <div className="trust-grid">
          {PILLARS.map((p) => (
            <div className="trust-card" key={p.title}>
              <span className="trust-icon">{p.icon}</span>
              <h3 className="trust-card-title">{p.title}</h3>
              <p className="trust-card-desc">{p.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
