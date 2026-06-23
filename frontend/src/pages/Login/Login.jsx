import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import '../auth.css';

const Login = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const [showPassword, setShowPassword] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const response = await api.post('/auth/login', { email, password });
      login(response.data.user, response.data.access_token);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.detail || 'Unable to connect to server');
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
            <h1 className="panel-heading">Financial intelligence<br />for modern India.</h1>
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
            <h2 className="auth-card-title">Welcome back</h2>
            <p className="auth-card-subtitle">Access your financial dashboard.</p>
          </div>

          <form onSubmit={handleSubmit} className="auth-form">
            <div className="field">
              <label htmlFor="email" className="field-label">
                Email
              </label>
              <input
                type="email"
                id="email"
                className="field-input"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            <div className="field">
              <label htmlFor="password" className="field-label">
                Password
              </label>
              <div className="password-field">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  className="field-input"
                  placeholder="Enter the password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
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
            </div>

            {error && <div className="form-error">{error}</div>}

            <button type="submit" className="submit-btn" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <p className="auth-switch">
            Don&apos;t have an account?{' '}
            <a href="/signup">Create account</a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default Login;
