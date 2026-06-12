import { Outlet } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import { SidebarProvider, useSidebar } from '../../context/SidebarContext';
import EmailVerificationBanner from '../../components/EmailVerificationBanner/EmailVerificationBanner';
import './DashboardLayout.css';

function Layout() {
  const { mobileOpen, closeMobile } = useSidebar();

  return (
    <div className="dashboard-shell">
      <Sidebar />
      {mobileOpen && (
        <div className="sidebar-overlay" onClick={closeMobile} aria-hidden="true" />
      )}
      <main className="dashboard-main">
        <EmailVerificationBanner />
        <Outlet />
      </main>
    </div>
  );
}

export default function DashboardLayout() {
  return (
    <SidebarProvider>
      <Layout />
    </SidebarProvider>
  );
}
