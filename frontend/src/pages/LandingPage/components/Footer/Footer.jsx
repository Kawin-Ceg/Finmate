import './Footer.css';

const LINKS = [
  {
    heading: 'Product',
    items: [
      { label: 'Features', href: '#features' },
      { label: 'How it works', href: '#how-it-works' },
      { label: 'Security', href: '#security' },
    ],
  },
  {
    heading: 'Account',
    items: [
      { label: 'Log in', href: '/login' },
      { label: 'Get started', href: '/signup' },
    ],
  },
];

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-top">
          <div className="footer-brand">
            <a href="/" className="footer-logo">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <rect width="24" height="24" rx="6" fill="#2563EB" />
                <path
                  d="M6 17L6 10L12 6L18 10L18 17L14 17L14 12L10 12L10 17Z"
                  fill="white"
                />
              </svg>
              <span>FinMate</span>
            </a>
            <p className="footer-tagline">
              AI-powered personal financial intelligence.
              <br />
              Built for India.
            </p>
          </div>

          {LINKS.map((group) => (
            <div className="footer-col" key={group.heading}>
              <h4 className="footer-col-heading">{group.heading}</h4>
              <ul className="footer-col-links">
                {group.items.map((item) => (
                  <li key={item.label}>
                    <a href={item.href} className="footer-link">
                      {item.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="footer-bottom">
          <p className="footer-copy">© 2026 FinMate. All rights reserved.</p>
          <p className="footer-credit">Built by Kawin A N</p>
        </div>
      </div>
    </footer>
  );
}
