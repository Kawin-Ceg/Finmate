import { useState, useEffect } from 'react';
import './Navbar.css';

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 16);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  const close = () => setMenuOpen(false);

  return (
    <header className={`nav${scrolled ? ' nav--scrolled' : ''}`}>
      <div className="nav-inner">
        <a href="/" className="nav-logo" onClick={close}>
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
            <rect width="24" height="24" rx="6" fill="#2563EB" />
            <path
              d="M6 17L6 10L12 6L18 10L18 17L14 17L14 12L10 12L10 17Z"
              fill="white"
            />
          </svg>
          <span className="nav-logo-text">FinMate</span>
        </a>

        <nav className={`nav-menu${menuOpen ? ' nav-menu--open' : ''}`} id="nav-menu">
          <a href="#features" className="nav-link" onClick={close}>Features</a>
          <a href="#how-it-works" className="nav-link" onClick={close}>How it works</a>
          <a href="#security" className="nav-link" onClick={close}>Security</a>
        </nav>

        <div className={`nav-actions${menuOpen ? ' nav-actions--open' : ''}`}>
          <a href="/login" className="nav-login" onClick={close}>Log in</a>
          <a href="/signup" className="nav-cta" onClick={close}>Get started</a>
        </div>

        <button
          className={`nav-toggle${menuOpen ? ' nav-toggle--open' : ''}`}
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle menu"
          aria-expanded={menuOpen}
        >
          <span />
          <span />
          <span />
        </button>
      </div>
    </header>
  );
}
