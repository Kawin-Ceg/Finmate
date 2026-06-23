import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard, ArrowLeftRight, Wallet, BarChart2,
  AlertTriangle, MessageCircle, Settings, LogOut, ChevronLeft, ChevronRight, User,
} from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';
import { useSidebar } from '../../../context/SidebarContext';
import './Sidebar.css';

const NAV_ITEMS = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/dashboard/transactions', icon: ArrowLeftRight, label: 'Transactions' },
  { to: '/dashboard/budgets', icon: Wallet, label: 'Budgets' },
  { to: '/dashboard/analytics', icon: BarChart2, label: 'Analytics' },
  { to: '/dashboard/anomalies', icon: AlertTriangle, label: 'Anomalies' },
  { to: '/dashboard/mate', icon: MessageCircle, label: 'Mate' },
];

const BOTTOM_ITEMS = [
  { to: '/dashboard/profile', icon: User, label: 'Profile' },
  { to: '/dashboard/settings', icon: Settings, label: 'Settings' },
];

function getInitials(name) {
  if (!name) return 'U';
  return name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2);
}

function Avatar({ user, size = 28 }) {
  const API_BASE = 'http://localhost:8000';
  if (user?.avatar_url) {
    const src = user.avatar_url.startsWith('http')
      ? user.avatar_url
      : `${API_BASE}${user.avatar_url}`;
    return (
      <img
        src={src}
        alt={user.name}
        className="sidebar-avatar sidebar-avatar--img"
        style={{ width: size, height: size }}
      />
    );
  }
  return (
    <div className="sidebar-avatar" style={{ width: size, height: size, fontSize: size * 0.38 }}>
      {getInitials(user?.name)}
    </div>
  );
}

export default function Sidebar() {
  const { user, logout } = useAuth();
  const { collapsed, toggle, mobileOpen, closeMobile } = useSidebar();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside className={[
      'sidebar',
      collapsed ? 'sidebar--collapsed' : '',
      mobileOpen ? 'sidebar--mobile-open' : '',
    ].join(' ').trim()}>
      <div className="sidebar-header">
        <a href="/" className="sidebar-logo" title="FinMate">
          <div className="sidebar-logo-icon">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <rect width="24" height="24" rx="6" fill="#2563EB" />
              <path d="M6 17L6 10L12 6L18 10L18 17L14 17L14 12L10 12L10 17Z" fill="white" />
            </svg>
          </div>
          <span className="sidebar-logo-name">FinMate</span>
        </a>
        <button
          className="sidebar-toggle"
          onClick={toggle}
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {collapsed
            ? <ChevronRight size={13} strokeWidth={2.5} />
            : <ChevronLeft size={13} strokeWidth={2.5} />
          }
        </button>
      </div>

      <nav className="sidebar-nav">
        {NAV_ITEMS.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            title={collapsed ? label : undefined}
            onClick={closeMobile}
            className={({ isActive }) =>
              `sidebar-link${isActive ? ' sidebar-link--active' : ''}`
            }
          >
            <Icon size={15} strokeWidth={1.75} className="sidebar-link-icon" />
            <span className="sidebar-link-label">{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="sidebar-divider" />

        <nav className="sidebar-bottom-nav">
          {BOTTOM_ITEMS.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              title={collapsed ? label : undefined}
              onClick={closeMobile}
              className={({ isActive }) =>
                `sidebar-link${isActive ? ' sidebar-link--active' : ''}`
              }
            >
              <Icon size={15} strokeWidth={1.75} className="sidebar-link-icon" />
              <span className="sidebar-link-label">{label}</span>
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-divider" style={{ marginTop: 6 }} />

        <div className="sidebar-user" title={collapsed ? user?.name : undefined}>
          <Avatar user={user} size={28} />
          <div className="sidebar-user-info">
            <span className="sidebar-user-name">{user?.name || 'User'}</span>
            <span className="sidebar-user-email">{user?.email || ''}</span>
          </div>
        </div>
        <button
          className="sidebar-logout"
          onClick={handleLogout}
          title={collapsed ? 'Sign out' : undefined}
        >
          <LogOut size={14} strokeWidth={1.75} className="sidebar-link-icon" />
          <span className="sidebar-link-label">Sign out</span>
        </button>
      </div>
    </aside>
  );
}
