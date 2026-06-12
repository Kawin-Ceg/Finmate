import { useEffect } from 'react';
import Navbar from './components/Navbar/Navbar';
import Hero from './components/Hero/Hero';
import Features from './components/Features/Features';
import HowItWorks from './components/HowItWorks/HowItWorks';
import AIShowcase from './components/AIShowcase/AIShowcase';
import Trust from './components/Trust/Trust';
import CTASection from './components/CTASection/CTASection';
import Footer from './components/Footer/Footer';
import './LandingPage.css';

export default function LandingPage() {
  useEffect(() => {
    const handleAnchorClick = (e) => {
      const target = e.target.closest('a[href^="#"]');
      if (!target) return;
      e.preventDefault();
      const id = target.getAttribute('href').slice(1);
      const el = document.getElementById(id);
      if (el) {
        const offset = 68;
        const top = el.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    };
    document.addEventListener('click', handleAnchorClick);
    return () => document.removeEventListener('click', handleAnchorClick);
  }, []);

  return (
    <div className="landing">
      <Navbar />
      <main>
        <Hero />
        <Features />
        <HowItWorks />
        <AIShowcase />
        <Trust />
        <CTASection />
      </main>
      <Footer />
    </div>
  );
}
