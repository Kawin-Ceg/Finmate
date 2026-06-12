import './HowItWorks.css';

const STEPS = [
  {
    num: '01',
    title: 'Upload your statement',
    description:
      'Export a PDF or CSV from your bank app. No account linking, no OAuth — just upload the file directly.',
    detail: 'Supports all major Indian banks: SBI, HDFC, ICICI, Axis, Kotak, and more.',
  },
  {
    num: '02',
    title: 'Auto-categorization',
    description:
      'FinMate\'s ML model reads every transaction and assigns it to one of 12+ spending categories in seconds.',
    detail: '95%+ accuracy on Indian merchant names with continuous improvement.',
  },
  {
    num: '03',
    title: 'AI analysis',
    description:
      'Patterns are extracted, budgets are computed, anomalies are flagged, and your financial health score is calculated.',
    detail: 'Powered by Isolation Forest for anomaly detection and FAISS-based vector retrieval.',
  },
  {
    num: '04',
    title: 'Personalized insights',
    description:
      'You receive a curated set of AI-generated insights, spending alerts, and recommendations tailored to your actual habits.',
    detail: 'Ask follow-up questions via the AI assistant using plain language.',
  },
];

export default function HowItWorks() {
  return (
    <section className="hiw" id="how-it-works">
      <div className="hiw-inner">
        <div className="hiw-header">
          <span className="section-eyebrow">How it works</span>
          <h2 className="hiw-title">From statement to insights in seconds</h2>
          <p className="hiw-sub">
            No integrations, no bank access. Upload once, understand everything.
          </p>
        </div>

        <div className="hiw-steps">
          {STEPS.map((step, i) => (
            <div className="hiw-step" key={step.num}>
              <div className="hiw-step-connector">
                <div className="hiw-step-num">{step.num}</div>
                {i < STEPS.length - 1 && <div className="hiw-step-line" />}
              </div>
              <div className="hiw-step-content">
                <h3 className="hiw-step-title">{step.title}</h3>
                <p className="hiw-step-desc">{step.description}</p>
                <span className="hiw-step-detail">{step.detail}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
