import { createContext, useContext, useEffect, useState } from 'react';
import { getSettings } from '../services/settingsService';
import { useAuth } from './AuthContext';

const SettingsContext = createContext(null);

const DEFAULTS = { currency: 'INR', dateFormat: 'DD/MM/YYYY', timezone: 'Asia/Kolkata' };

function toLocal(s) {
  return {
    currency: s.currency || DEFAULTS.currency,
    dateFormat: s.date_format || DEFAULTS.dateFormat,
    timezone: s.timezone || DEFAULTS.timezone,
  };
}

export function SettingsProvider({ children }) {
  const { user } = useAuth();
  const [settings, setSettings] = useState(DEFAULTS);

  const refreshSettings = () => {
    if (!user) return Promise.resolve();
    return getSettings()
      .then((s) => setSettings(toLocal(s)))
      .catch(() => setSettings(DEFAULTS));
  };

  useEffect(() => {
    if (!user) {
      setSettings(DEFAULTS);
      return;
    }
    refreshSettings();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  return (
    <SettingsContext.Provider value={{ ...settings, refreshSettings }}>
      {children}
    </SettingsContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useSettings() {
  return useContext(SettingsContext);
}
