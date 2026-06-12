import { useState } from 'react';
import { MailCheck, X, Send, Loader } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { sendVerificationOTP } from '../../services/profileService';
import './EmailVerificationBanner.css';

export default function EmailVerificationBanner() {
  const { user, updateUser } = useAuth();
  const [dismissed, setDismissed] = useState(false);
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState('');

  if (!user || user.email_verified || dismissed) return null;

  const handleSend = async () => {
    setSending(true);
    setError('');
    try {
      await sendVerificationOTP();
      setSent(true);
    } catch (e) {
      const msg = e?.response?.data?.detail || 'Failed to send code.';
      setError(msg);
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="evb-banner">
      <div className="evb-icon">
        <MailCheck size={16} />
      </div>
      <div className="evb-body">
        <span className="evb-text">
          {sent
            ? 'Verification code sent! Check your inbox and go to Settings → Security to verify.'
            : 'Please verify your email address to secure your account.'}
        </span>
        {error && <span className="evb-error">{error}</span>}
      </div>
      {!sent && (
        <button className="evb-action" onClick={handleSend} disabled={sending}>
          {sending ? <Loader size={13} className="spin" /> : <Send size={13} />}
          {sending ? 'Sending…' : 'Send Code'}
        </button>
      )}
      <button className="evb-close" onClick={() => setDismissed(true)} aria-label="Dismiss">
        <X size={14} />
      </button>
    </div>
  );
}
