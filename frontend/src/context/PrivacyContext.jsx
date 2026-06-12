import { createContext, useContext, useState } from 'react';

const PrivacyContext = createContext(null);

export function PrivacyProvider({ children }) {
  const [privacyMode, setPrivacyMode] = useState(
    () => localStorage.getItem('fm-privacy') === 'true'
  );

  const toggle = () => {
    setPrivacyMode((prev) => {
      const next = !prev;
      localStorage.setItem('fm-privacy', String(next));
      return next;
    });
  };

  const mask = (value) => (privacyMode ? '₹••••' : value);

  return (
    <PrivacyContext.Provider value={{ privacyMode, toggle, mask }}>
      {children}
    </PrivacyContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function usePrivacy() {
  return useContext(PrivacyContext);
}
