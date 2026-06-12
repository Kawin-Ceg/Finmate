import { createContext, useContext, useState, useEffect } from 'react';

const SidebarContext = createContext(null);

export function SidebarProvider({ children }) {
  const [collapsed, setCollapsed] = useState(() => {
    return localStorage.getItem('fm-sidebar') === 'collapsed';
  });
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle('sidebar-collapsed', collapsed);
  }, [collapsed]);

  const toggle = () => {
    setCollapsed(c => {
      const next = !c;
      localStorage.setItem('fm-sidebar', next ? 'collapsed' : 'expanded');
      return next;
    });
  };

  const openMobile = () => setMobileOpen(true);
  const closeMobile = () => setMobileOpen(false);

  return (
    <SidebarContext.Provider value={{ collapsed, toggle, mobileOpen, openMobile, closeMobile }}>
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebar() {
  const ctx = useContext(SidebarContext);
  if (!ctx) throw new Error('useSidebar must be used within SidebarProvider');
  return ctx;
}
