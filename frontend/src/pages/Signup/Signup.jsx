import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import '../auth.css';

const Signup = () => {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    confirm: '',
  });

  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [agreed, setAgreed] = useState(false);
  const [loading, setLoading] = useState(false);
  const [strength, setStrength] = useState(0);
  const [error, setError] = useState('');

  const update = (field) => (e) => {
    const value = e.target.value;
    setForm((prev) => ({ ...prev, [field]: value }));
    if (field === 'password') calculateStrength(value);
  };

  const calculateStrength = (password) => {
    let score = 0;
    if (password.length >= 8) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[a-z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;
    setStrength(score);
  };

  const getStrengthLabel = () => {
    if (!form.password) return '';
    if (strength <= 2) return 'Weak';
    if (strength <= 3) return 'Fair';
    if (strength <= 4) return 'Strong';
    return 'Excellent';
  };

  const getStrengthColor = () => {
    if (strength <= 2) return '#DC2626';
    if (strength <= 3) return '#D97706';
    if (strength <= 4) return '#059669';
    return '#047857';
  };

  const mismatch = form.confirm && form.password !== form.confirm;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!agreed) {
      setError('Please accept the terms and privacy policy.');
      return;
    }
    if (mismatch) {
      setError('Passwords do not match.');
      return;
    }
    setError('');
    try {
      setLoading(true);
      await api.post('/auth/signup', {
        name: form.name,
        email: form.email,
        password: form.password,
      });
      navigate('/login');
    } catch (err) {
      setError(err.response?.data?.detail || 'Server connection failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-panel">
        <div className="panel-content">
          <div className="panel-header">
            <a href="/" className="panel-logo">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <rect width="24" height="24" rx="6" fill="#2563EB" />
                <path
                  d="M6 17L6 10L12 6L18 10L18 17L14 17L14 12L10 12L10 17Z"
                  fill="white"
                />
              </svg>
              <span className="logo-word">FinMate</span>
            </a>
          </div>

          <div className="panel-hero">
            <h1 className="panel-heading">Start your financial<br />journey today.</h1>
            <p className="panel-description">
              Upload your bank statement once. Get complete clarity on where your money goes.
            </p>
          </div>

          <div className="panel-steps">
            <div className="panel-step">
              <span className="step-number">01</span>
              <div>
                <div className="step-title">Upload any bank statement</div>
                <div className="step-desc">CSV from HDFC, SBI, ICICI, Axis — any format works.</div>
              </div>
            </div>
            <div className="panel-step">
              <span className="step-number">02</span>
              <div>
                <div className="step-title">Auto-categorize every transaction</div>
                <div className="step-desc">15 categories classified instantly. No manual entry.</div>
              </div>
            </div>
            <div className="panel-step">
              <span className="step-number">03</span>
              <div>
                <div className="step-title">Measure your financial health</div>
                <div className="step-desc">A 0–100 score with personalized insights.</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="auth-form-side">
        <div className="auth-card">
          <div className="auth-card-header">
            <div className="auth-card-logo">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <rect width="24" height="24" rx="6" fill="#2563EB" />
                <path
                  d="M6 17L6 10L12 6L18 10L18 17L14 17L14 12L10 12L10 17Z"
                  fill="white"
                />
              </svg>
            </div>
            <h2 className="auth-card-title">Create Account</h2>
            <p className="auth-card-subtitle">
              Start your journey toward smarter financial decisions.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="field">
              <label className="field-label">Full Name</label>
              <input
                className="field-input"
                type="text"
                value={form.name}
                onChange={update('name')}
                placeholder="John Doe"
                required
              />
            </div>

            <div className="field">
              <label className="field-label">Email</label>
              <input
                className="field-input"
                type="email"
                value={form.email}
                onChange={update('email')}
                placeholder="john@example.com"
                required
              />
            </div>

            <div className="field">
              <label className="field-label">Password</label>
              <div className="password-field">
                <input
                  className="field-input"
                  type={showPassword ? 'text' : 'password'}
                  value={form.password}
                  onChange={update('password')}
                  placeholder="Create password"
                  required
                />
                <button
                  type="button"
                  className="toggle-password"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
              {form.password && (
                <div className="strength-meter">
                  <div className="strength-bar">
                    <div
                      className="strength-fill"
                      style={{
                        width: `${(strength / 5) * 100}%`,
                        backgroundColor: getStrengthColor(),
                      }}
                    />
                  </div>
                  <span
                    className="strength-label"
                    style={{ color: getStrengthColor() }}
                  >
                    {getStrengthLabel()}
                  </span>
                </div>
              )}
            </div>

            <div className="field">
              <label className="field-label">Confirm Password</label>
              <div className="password-field">
                <input
                  className={`field-input ${mismatch ? 'input-error' : ''}`}
                  type={showConfirm ? 'text' : 'password'}
                  value={form.confirm}
                  onChange={update('confirm')}
                  placeholder="Confirm password"
                  required
                />
                <button
                  type="button"
                  className="toggle-password"
                  onClick={() => setShowConfirm(!showConfirm)}
                >
                  {showConfirm ? 'Hide' : 'Show'}
                </button>
              </div>
              {mismatch && (
                <span className="error-msg">Passwords do not match</span>
              )}
            </div>

            <label className="terms">
              <input
                type="checkbox"
                checked={agreed}
                onChange={(e) => setAgreed(e.target.checked)}
              />
              <span>I agree to the Terms and Privacy Policy</span>
            </label>

            {error && <div className="form-error">{error}</div>}

            <button type="submit" className="submit-btn" disabled={loading}>
              {loading ? 'Creating Account...' : 'Create Account'}
            </button>
          </form>

          <p className="auth-switch">
            Already have an account?{' '}
            <a href="/login">Sign In</a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Signup;

