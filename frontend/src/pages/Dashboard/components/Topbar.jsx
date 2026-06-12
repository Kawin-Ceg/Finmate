import { Bell, Menu } from 'lucide-react';
import { useAuth } from '../../../context/AuthContext';
import { useSidebar } from '../../../context/SidebarContext';
import './Topbar.css';

function getInitials(name) {
  if (!name) return 'U';
  return name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2);
}

export default function Topbar({ title }) {
  const { user } = useAuth();
  const { openMobile } = useSidebar();

  return (
    <header className="topbar">
      <button
        className="topbar-menu-btn"
        onClick={openMobile}
        aria-label="Open menu"
      >
        <Menu size={18} strokeWidth={1.75} />
      </button>

      <div className="topbar-left">
        <h1 className="topbar-title">{title}</h1>
      </div>

      <div className="topbar-right">
        <button className="topbar-btn" aria-label="Notifications">
          <Bell size={15} strokeWidth={1.75} />
        </button>
        <div className="topbar-avatar" title={user?.name}>
          {getInitials(user?.name)}
        </div>
      </div>
    </header>
  );
}
