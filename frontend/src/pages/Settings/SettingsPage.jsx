import { useState, useEffect, useCallback } from 'react';
import {
  Settings, Sun, Moon, Monitor, Bell, Lock, Trash2, Download,
  ShieldCheck, Eye, EyeOff, Check, Loader, AlertCircle,
  RefreshCw, Globe, ChevronRight, LogOut, Smartphone, Clock,
} from 'lucide-react';
import Topbar from '../Dashboard/components/Topbar';
import { useTheme } from '../../context/ThemeContext';
import { usePrivacy } from '../../context/PrivacyContext';
import { useAuth } from '../../context/AuthContext';
import {
  getSettings, updateSettings, getSessions,
  revokeSession, revokeAllOtherSessions, exportData, deleteAccount,
} from '../../services/settingsService';
import {
  sendVerificationOTP, verifyEmail, changePassword,
  getSecurityScore,
} from '../../services/profileService';
import './SettingsPage.css';

const TABS = [
  { id: 'general',      label: 'General',      icon: Settings },
  { id: 'appearance',   label: 'Appearance',   icon: Sun },
  { id: 'notifications',label: 'Notifications',icon: Bell },
  { id: 'privacy',      label: 'Privacy',      icon: Eye },
  { id: 'security',     label: 'Security',     icon: Lock },
  { id: 'account',      label: 'Account',      icon: Trash2 },
];

const CURRENCIES = ['INR', 'USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'SGD'];
const DATE_FORMATS = ['DD/MM/YYYY', 'MM/DD/YYYY', 'YYYY-MM-DD'];
const TIMEZONES = [
  'Asia/Kolkata', 'UTC', 'America/New_York', 'America/Los_Angeles',
  'Europe/London', 'Europe/Paris', 'Asia/Tokyo', 'Australia/Sydney',
];

// ── Generic helpers ───────────────────────────────────────────

function Toggle({ on, onChange, disabled }) {
  return (
    <button
      className={`sg-toggle${on ? ' sg-toggle--on' : ''}`}
      onClick={() => onChange(!on)}
      disabled={disabled}
      role="switch"
      aria-checked={on}
    >
      <span className="sg-toggle-thumb" />
    </button>
  );
}

function Select({ value, onChange, options, label }) {
  return (
    <div className="sg-field">
      {label && <label className="sg-label">{label}</label>}
      <select className="sg-select" value={value} onChange={(e) => onChange(e.target.value)}>
        {options.map((o) => (
          <option key={typeof o === 'string' ? o : o.value} value={typeof o === 'string' ? o : o.value}>
            {typeof o === 'string' ? o : o.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function SettingRow({ label, description, children }) {
  return (
    <div className="sg-row">
      <div className="sg-row-text">
        <span className="sg-row-label">{label}</span>
        {description && <span className="sg-row-desc">{description}</span>}
      </div>
      <div className="sg-row-control">{children}</div>
    </div>
  );
}

function SectionCard({ title, description, children }) {
  return (
    <div className="sg-section">
      <div className="sg-section-head">
        <h3 className="sg-section-title">{title}</h3>
        {description && <p className="sg-section-desc">{description}</p>}
      </div>
      <div className="sg-section-body">{children}</div>
    </div>
  );
}

// ── Tabs ─────────────────────────────────────────────────────

function GeneralTab({ settings, onChange, saving }) {
  return (
    <SectionCard title="General Preferences" description="Configure regional and display options.">
      <SettingRow label="Currency" description="Used throughout analytics and budgets.">
        <select className="sg-select sg-select--sm" value={settings.currency} onChange={(e) => onChange({ currency: e.target.value })} disabled={saving}>
          {CURRENCIES.map((c) => <option key={c}>{c}</option>)}
        </select>
      </SettingRow>
      <SettingRow label="Date Format" description="How dates appear across reports.">
        <select className="sg-select sg-select--sm" value={settings.date_format} onChange={(e) => onChange({ date_format: e.target.value })} disabled={saving}>
          {DATE_FORMATS.map((f) => <option key={f}>{f}</option>)}
        </select>
      </SettingRow>
      <SettingRow label="Timezone" description="Used in scheduled reports.">
        <select className="sg-select sg-select--sm" value={settings.timezone} onChange={(e) => onChange({ timezone: e.target.value })} disabled={saving}>
          {TIMEZONES.map((t) => <option key={t}>{t}</option>)}
        </select>
      </SettingRow>
    </SectionCard>
  );
}

function AppearanceTab({ settings, onChange, saving }) {
  const { theme, setTheme } = useTheme();

  const THEMES = [
    { id: 'light',  label: 'Light',   Icon: Sun,     desc: 'Clean and bright' },
    { id: 'dark',   label: 'Dark',    Icon: Moon,    desc: 'Easy on the eyes' },
    { id: 'system', label: 'System',  Icon: Monitor, desc: 'Follows your OS' },
  ];

  const handleTheme = (t) => {
    setTheme(t);
    onChange({ theme: t });
  };

  return (
    <SectionCard title="Appearance" description="Choose how FinMate looks.">
      <div className="sg-theme-grid">
        {THEMES.map(({ id, label, Icon, desc }) => (
          <button
            key={id}
            className={`sg-theme-card${theme === id ? ' sg-theme-card--active' : ''}`}
            onClick={() => handleTheme(id)}
          >
            <div className="sg-theme-icon">
              <Icon size={20} />
            </div>
            <span className="sg-theme-label">{label}</span>
            <span className="sg-theme-desc">{desc}</span>
            {theme === id && <Check size={14} className="sg-theme-check" />}
          </button>
        ))}
      </div>
    </SectionCard>
  );
}

function NotificationsTab({ settings, onChange, saving }) {
  const rows = [
    { key: 'notif_budget_alerts',      label: 'Budget Alerts',         desc: 'When you approach or exceed a budget limit' },
    { key: 'notif_anomaly_alerts',     label: 'Anomaly Alerts',        desc: 'Unusual spending patterns detected' },
    { key: 'notif_monthly_reports',    label: 'Monthly Reports',       desc: 'Summary of your finances each month' },
    { key: 'notif_financial_insights', label: 'Financial Insights',    desc: 'AI-powered spending tips and patterns' },
    { key: 'notif_product_updates',    label: 'Product Updates',       desc: 'New features and improvements' },
  ];

  return (
    <SectionCard title="Notification Preferences" description="Control what FinMate notifies you about.">
      {rows.map(({ key, label, desc }) => (
        <SettingRow key={key} label={label} description={desc}>
          <Toggle on={settings[key]} onChange={(v) => onChange({ [key]: v })} disabled={saving} />
        </SettingRow>
      ))}
    </SectionCard>
  );
}

function PrivacyTab({ settings, onChange, saving }) {
  const { privacyMode, toggle } = usePrivacy();

  return (
    <>
      <SectionCard title="Privacy Mode" description="Hide financial values from prying eyes.">
        <SettingRow
          label="Privacy Mode"
          description='Replaces all monetary values with "₹••••" until you reveal them.'
        >
          <Toggle on={privacyMode} onChange={toggle} />
        </SettingRow>
      </SectionCard>

      <SectionCard title="Display Options" description="Control what is shown on your dashboard.">
        <SettingRow label="Show Balances" description="Display account balance on dashboard.">
          <Toggle on={settings.privacy_show_balances} onChange={(v) => onChange({ privacy_show_balances: v })} disabled={saving} />
        </SettingRow>
        <SettingRow label="Show Spending Amounts" description="Show exact amounts in transaction lists.">
          <Toggle on={settings.privacy_show_amounts} onChange={(v) => onChange({ privacy_show_amounts: v })} disabled={saving} />
        </SettingRow>
        <SettingRow label="Mask Sensitive Values" description="Blur analytics charts when screen is shared.">
          <Toggle on={settings.privacy_mask_values} onChange={(v) => onChange({ privacy_mask_values: v })} disabled={saving} />
        </SettingRow>
      </SectionCard>
    </>
  );
}

function SecurityTab({ user, updateUser }) {
  const [otpSent, setOtpSent] = useState(false);
  const [otp, setOtp] = useState('');
  const [verifying, setVerifying] = useState(false);
  const [sendingOtp, setSendingOtp] = useState(false);
  const [scoreData, setScoreData] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loadingSessions, setLoadingSessions] = useState(true);

  // Password change
  const [pwForm, setPwForm] = useState({ current_password: '', new_password: '', confirm_password: '' });
  const [changingPw, setChangingPw] = useState(false);
  const [showPw, setShowPw] = useState(false);

  const [msg, setMsg] = useState({ text: '', type: '' });

  const flash = (text, type = 'success') => {
    setMsg({ text, type });
    setTimeout(() => setMsg({ text: '', type: '' }), 4000);
  };

  useEffect(() => {
    getSecurityScore().then(setScoreData).catch(() => {});
    getSessions()
      .then(setSessions)
      .catch(() => {})
      .finally(() => setLoadingSessions(false));
  }, []);

  const handleSendOtp = async () => {
    setSendingOtp(true);
    try {
      await sendVerificationOTP();
      setOtpSent(true);
      flash('Verification code sent to your email.');
    } catch (e) {
      flash(e?.response?.data?.detail || 'Failed to send code.', 'error');
    } finally {
      setSendingOtp(false);
    }
  };

  const handleVerify = async () => {
    if (otp.length !== 6) { flash('Enter the 6-digit code.', 'error'); return; }
    setVerifying(true);
    try {
      await verifyEmail(otp);
      updateUser({ email_verified: true });
      flash('Email verified successfully!');
      setOtpSent(false);
      setOtp('');
    } catch (e) {
      flash(e?.response?.data?.detail || 'Verification failed.', 'error');
    } finally {
      setVerifying(false);
    }
  };

  const handleChangePassword = async () => {
    setChangingPw(true);
    try {
      await changePassword(pwForm);
      flash('Password updated successfully.');
      setPwForm({ current_password: '', new_password: '', confirm_password: '' });
    } catch (e) {
      flash(e?.response?.data?.detail || 'Password change failed.', 'error');
    } finally {
      setChangingPw(false);
    }
  };

  const handleRevokeSession = async (id) => {
    try {
      await revokeSession(id);
      setSessions((s) => s.filter((x) => x.id !== id));
      flash('Session revoked.');
    } catch (e) {
      flash(e?.response?.data?.detail || 'Failed to revoke session.', 'error');
    }
  };

  const handleRevokeAll = async () => {
    try {
      await revokeAllOtherSessions();
      setSessions((s) => s.filter((x) => x.is_current));
      flash('All other sessions revoked.');
    } catch {
      flash('Failed.', 'error');
    }
  };

  const scoreColor = scoreData
    ? (scoreData.score >= 80 ? '#10b981' : scoreData.score >= 60 ? '#f59e0b' : '#ef4444')
    : '#94a3b8';

  return (
    <>
      {msg.text && (
        <div className={`sg-toast sg-toast--${msg.type}`}>
          {msg.type === 'success' ? <Check size={14} /> : <AlertCircle size={14} />}
          {msg.text}
        </div>
      )}

      {/* Security Score */}
      {scoreData && (
        <SectionCard title="Account Security Score">
          <div className="sg-score-row">
            <div className="sg-score-bar-wrap">
              <div className="sg-score-bar" style={{ width: `${scoreData.score}%`, background: scoreColor }} />
            </div>
            <span className="sg-score-num" style={{ color: scoreColor }}>{scoreData.score}/100</span>
            <span className="sg-score-grade">{scoreData.grade}</span>
          </div>
          {scoreData.factors.length > 0 && (
            <div className="sg-score-hints">
              {scoreData.factors.map((f, i) => (
                <div key={i} className="sg-score-hint">
                  <AlertCircle size={12} />
                  <span>{f.text}</span>
                  <span className="sg-hint-pts">{f.impact}</span>
                </div>
              ))}
            </div>
          )}
        </SectionCard>
      )}

      {/* Email Verification */}
      <SectionCard title="Email Verification" description="Verify your email to secure your account.">
        {user?.email_verified ? (
          <div className="sg-verified-row">
            <ShieldCheck size={18} color="#10b981" />
            <div>
              <span className="sg-verified-label">Your email is verified</span>
              <p className="sg-verified-sub">{user.email}</p>
            </div>
          </div>
        ) : (
          <div className="sg-verify-box">
            <p className="sg-verify-desc">Your email is not yet verified. This is required for account security.</p>
            {!otpSent ? (
              <button className="sg-action-btn" onClick={handleSendOtp} disabled={sendingOtp}>
                {sendingOtp ? <><Loader size={13} className="spin" /> Sending…</> : 'Send Verification Code'}
              </button>
            ) : (
              <div className="sg-otp-row">
                <input
                  className="sg-otp-input"
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="000000"
                  maxLength={6}
                />
                <button className="sg-action-btn" onClick={handleVerify} disabled={verifying}>
                  {verifying ? <><Loader size={13} className="spin" /> Verifying…</> : 'Verify'}
                </button>
                <button className="sg-link-btn" onClick={handleSendOtp} disabled={sendingOtp}>
                  Resend
                </button>
              </div>
            )}
          </div>
        )}
      </SectionCard>

      {/* Password Change */}
      <SectionCard title="Change Password" description="Use a strong password to protect your account.">
        <div className="sg-pw-form">
          {['current_password', 'new_password', 'confirm_password'].map((k) => (
            <div className="sg-field" key={k}>
              <label className="sg-label">
                {k === 'current_password' ? 'Current Password'
                  : k === 'new_password' ? 'New Password'
                  : 'Confirm New Password'}
              </label>
              <div className="sg-pw-wrap">
                <input
                  type={showPw ? 'text' : 'password'}
                  className="sg-input"
                  value={pwForm[k]}
                  onChange={(e) => setPwForm((f) => ({ ...f, [k]: e.target.value }))}
                  placeholder="••••••••"
                />
                {k === 'new_password' && (
                  <button className="sg-pw-eye" onClick={() => setShowPw((p) => !p)}>
                    {showPw ? <EyeOff size={14} /> : <Eye size={14} />}
                  </button>
                )}
              </div>
            </div>
          ))}
          <button className="sg-action-btn" onClick={handleChangePassword} disabled={changingPw}>
            {changingPw ? <><Loader size={13} className="spin" /> Updating…</> : 'Update Password'}
          </button>
        </div>
      </SectionCard>

      {/* Active Sessions */}
      <SectionCard title="Active Sessions" description="Devices currently signed into your account.">
        {loadingSessions ? (
          <p className="sg-muted">Loading sessions…</p>
        ) : sessions.length === 0 ? (
          <p className="sg-muted">No active sessions found.</p>
        ) : (
          <>
            <div className="sg-sessions">
              {sessions.map((s) => (
                <div key={s.id} className={`sg-session${s.is_current ? ' sg-session--current' : ''}`}>
                  <Smartphone size={15} className="sg-session-icon" />
                  <div className="sg-session-info">
                    <span className="sg-session-device">
                      {s.device_info?.slice(0, 60) || 'Unknown device'}
                      {s.is_current && <span className="sg-current-badge">Current</span>}
                    </span>
                    <span className="sg-session-meta">
                      <Clock size={11} /> {s.created_at ? new Date(s.created_at).toLocaleString('en-IN') : '—'}
                      &nbsp;·&nbsp; {s.ip_address || '—'}
                    </span>
                  </div>
                  {!s.is_current && (
                    <button className="sg-revoke-btn" onClick={() => handleRevokeSession(s.id)}>
                      Revoke
                    </button>
                  )}
                </div>
              ))}
            </div>
            {sessions.filter((s) => !s.is_current).length > 0 && (
              <button className="sg-link-btn sg-link-btn--danger" onClick={handleRevokeAll}>
                Sign out all other sessions
              </button>
            )}
          </>
        )}
      </SectionCard>
    </>
  );
}

function AccountTab({ user, logout, navigate }) {
  const [delPass, setDelPass] = useState('');
  const [showDelModal, setShowDelModal] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [exporting, setExporting] = useState('');
  const [msg, setMsg] = useState('');

  const flash = (text) => { setMsg(text); setTimeout(() => setMsg(''), 3000); };

  const handleExport = async (format) => {
    setExporting(format);
    try {
      const blob = await exportData(format);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = format === 'json' ? 'finmate_export.json' : 'finmate_transactions.csv';
      a.click();
      URL.revokeObjectURL(url);
      flash(`${format.toUpperCase()} exported successfully.`);
    } catch {
      flash('Export failed.');
    } finally {
      setExporting('');
    }
  };

  const handleDelete = async () => {
    if (!delPass) return;
    setDeleting(true);
    try {
      await deleteAccount(delPass);
      logout();
    } catch (e) {
      flash(e?.response?.data?.detail || 'Deletion failed. Check your password.');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <>
      {msg && <div className="sg-toast sg-toast--success"><Check size={14} />{msg}</div>}

      <SectionCard title="Export Your Data" description="Download a copy of all your financial data.">
        <div className="sg-export-grid">
          <div className="sg-export-card">
            <div className="sg-export-icon"><Download size={20} /></div>
            <div className="sg-export-info">
              <span className="sg-export-label">CSV Export</span>
              <span className="sg-export-desc">All transactions in spreadsheet format</span>
            </div>
            <button className="sg-action-btn sg-action-btn--sm" onClick={() => handleExport('csv')} disabled={!!exporting}>
              {exporting === 'csv' ? <Loader size={12} className="spin" /> : 'Download'}
            </button>
          </div>
          <div className="sg-export-card">
            <div className="sg-export-icon"><Download size={20} /></div>
            <div className="sg-export-info">
              <span className="sg-export-label">JSON Export</span>
              <span className="sg-export-desc">Full data including budgets and settings</span>
            </div>
            <button className="sg-action-btn sg-action-btn--sm" onClick={() => handleExport('json')} disabled={!!exporting}>
              {exporting === 'json' ? <Loader size={12} className="spin" /> : 'Download'}
            </button>
          </div>
        </div>
      </SectionCard>

      <SectionCard title="Danger Zone">
        <div className="sg-danger-zone">
          <div className="sg-danger-row">
            <div>
              <span className="sg-danger-label">Delete Account</span>
              <p className="sg-danger-desc">
                Permanently delete your account and all associated data. This action cannot be undone.
              </p>
            </div>
            <button className="sg-danger-btn" onClick={() => setShowDelModal(true)}>
              <Trash2 size={13} /> Delete Account
            </button>
          </div>
        </div>
      </SectionCard>

      {/* Delete Modal */}
      {showDelModal && (
        <div className="sg-modal-overlay" onClick={() => setShowDelModal(false)}>
          <div className="sg-modal" onClick={(e) => e.stopPropagation()}>
            <h3 className="sg-modal-title">Delete Account</h3>
            <p className="sg-modal-body">
              This will permanently delete your account, all transactions, budgets, and analytics data.
              <strong> This cannot be undone.</strong>
            </p>
            <div className="sg-field" style={{ marginTop: 16 }}>
              <label className="sg-label">Confirm your password to proceed</label>
              <input
                type="password"
                className="sg-input"
                value={delPass}
                onChange={(e) => setDelPass(e.target.value)}
                placeholder="Enter your password"
              />
            </div>
            <div className="sg-modal-actions">
              <button className="sg-cancel-btn" onClick={() => setShowDelModal(false)}>Cancel</button>
              <button
                className="sg-danger-btn"
                onClick={handleDelete}
                disabled={!delPass || deleting}
              >
                {deleting ? <><Loader size={12} className="spin" /> Deleting…</> : 'Yes, Delete My Account'}
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

// ── Page ─────────────────────────────────────────────────────

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState('general');
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const { user, updateUser, logout } = useAuth();

  const loadSettings = useCallback(async () => {
    try {
      const s = await getSettings();
      setSettings(s);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadSettings(); }, [loadSettings]);

  const handleChange = async (patch) => {
    setSettings((prev) => ({ ...prev, ...patch }));
    setSaving(true);
    try {
      await updateSettings(patch);
    } catch {
      // revert on failure
      loadSettings();
    } finally {
      setSaving(false);
    }
  };

  const defaultSettings = {
    currency: 'INR', timezone: 'Asia/Kolkata', date_format: 'DD/MM/YYYY',
    theme: 'system',
    notif_budget_alerts: true, notif_anomaly_alerts: true,
    notif_monthly_reports: false, notif_financial_insights: false, notif_product_updates: false,
    privacy_show_balances: true, privacy_show_amounts: true,
    privacy_mask_values: false, privacy_mode: false,
    ...(settings || {}),
  };

  const renderTab = () => {
    if (loading) return <div className="sg-loading">Loading settings…</div>;
    switch (activeTab) {
      case 'general':       return <GeneralTab settings={defaultSettings} onChange={handleChange} saving={saving} />;
      case 'appearance':    return <AppearanceTab settings={defaultSettings} onChange={handleChange} saving={saving} />;
      case 'notifications': return <NotificationsTab settings={defaultSettings} onChange={handleChange} saving={saving} />;
      case 'privacy':       return <PrivacyTab settings={defaultSettings} onChange={handleChange} saving={saving} />;
      case 'security':      return <SecurityTab user={user} updateUser={updateUser} />;
      case 'account':       return <AccountTab user={user} logout={logout} />;
      default:              return null;
    }
  };

  return (
    <>
      <Topbar title="Settings" />
      <div className="sg-content">
        <div className="sg-layout">

          {/* Tab Sidebar */}
          <nav className="sg-tabs">
            {TABS.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                className={`sg-tab${activeTab === id ? ' sg-tab--active' : ''}`}
                onClick={() => setActiveTab(id)}
              >
                <Icon size={15} strokeWidth={1.75} />
                <span>{label}</span>
                {activeTab === id && <ChevronRight size={13} className="sg-tab-arrow" />}
              </button>
            ))}
          </nav>

          {/* Content */}
          <div className="sg-panel">
            {saving && <div className="sg-saving-indicator"><Loader size={12} className="spin" /> Saving…</div>}
            {renderTab()}
          </div>

        </div>
      </div>
    </>
  );
}
