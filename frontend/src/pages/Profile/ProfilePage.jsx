import { useState, useEffect, useRef } from 'react';
import {
  Camera, Trash2, Save, ShieldCheck, Mail, Calendar,
  MapPin, FileText, Check, Loader, AlertCircle,
} from 'lucide-react';
import Topbar from '../Dashboard/components/Topbar';
import {
  getProfile, updateProfile, uploadAvatar, deleteAvatar, getSecurityScore,
} from '../../services/profileService';
import { useAuth } from '../../context/AuthContext';
import './ProfilePage.css';

const API_BASE = 'http://localhost:8000';

function fmt(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('en-IN', {
    year: 'numeric', month: 'long', day: 'numeric',
  });
}

function AvatarSection({ profile, onUpload, onDelete, uploading }) {
  const inputRef = useRef();

  const src = profile?.avatar_url
    ? (profile.avatar_url.startsWith('http') ? profile.avatar_url : `${API_BASE}${profile.avatar_url}`)
    : null;

  return (
    <div className="prof-avatar-section">
      <div className="prof-avatar-wrap">
        {src ? (
          <img className="prof-avatar-img" src={src} alt={profile.name} />
        ) : (
          <div className="prof-avatar-placeholder">
            {profile?.name ? profile.name.slice(0, 1).toUpperCase() : 'U'}
          </div>
        )}
        <button
          className="prof-avatar-camera"
          onClick={() => inputRef.current?.click()}
          title="Upload photo"
        >
          {uploading ? <Loader size={13} className="spin" /> : <Camera size={13} />}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          style={{ display: 'none' }}
          onChange={(e) => e.target.files[0] && onUpload(e.target.files[0])}
        />
      </div>
      <div className="prof-avatar-meta">
        <p className="prof-avatar-name">{profile?.name}</p>
        <p className="prof-avatar-email">{profile?.email}</p>
        <div className="prof-avatar-actions">
          <button
            className="prof-btn prof-btn--sm"
            onClick={() => inputRef.current?.click()}
            disabled={uploading}
          >
            Change photo
          </button>
          {profile?.avatar_url && (
            <button
              className="prof-btn prof-btn--sm prof-btn--ghost"
              onClick={onDelete}
              disabled={uploading}
            >
              <Trash2 size={12} /> Remove
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

function SecurityScore({ data }) {
  if (!data) return null;
  const pct = data.score;
  const color = pct >= 80 ? '#10b981' : pct >= 60 ? '#f59e0b' : '#ef4444';
  const CIRC = 2 * Math.PI * 30;

  return (
    <div className="prof-score-card">
      <div className="prof-score-visual">
        <svg width="80" height="80" viewBox="0 0 80 80">
          <circle cx="40" cy="40" r="30" fill="none" stroke="var(--border)" strokeWidth="6" />
          <circle
            cx="40" cy="40" r="30" fill="none"
            stroke={color} strokeWidth="6"
            strokeDasharray={CIRC}
            strokeDashoffset={CIRC * (1 - pct / 100)}
            strokeLinecap="round"
            transform="rotate(-90 40 40)"
            style={{ transition: 'stroke-dashoffset 0.6s ease' }}
          />
        </svg>
        <div className="prof-score-num" style={{ color }}>
          <span>{pct}</span>
        </div>
      </div>
      <div className="prof-score-info">
        <h3 className="prof-score-grade">{data.grade}</h3>
        <p className="prof-score-label">Security Score</p>
        {data.factors.length > 0 && (
          <ul className="prof-score-factors">
            {data.factors.map((f, i) => (
              <li key={i}>
                <AlertCircle size={11} />
                <span>{f.text}</span>
                <span className="prof-factor-pts">{f.impact}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default function ProfilePage() {
  const { updateUser } = useAuth();
  const [profile, setProfile] = useState(null);
  const [score, setScore] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const [form, setForm] = useState({ name: '', country: '', bio: '' });

  useEffect(() => {
    Promise.all([getProfile(), getSecurityScore()])
      .then(([p, s]) => {
        setProfile(p);
        setScore(s);
        setForm({ name: p.name || '', country: p.country || '', bio: p.bio || '' });
      })
      .catch(() => setError('Failed to load profile.'))
      .finally(() => setLoading(false));
  }, []);

  const flash = (msg, isErr = false) => {
    if (isErr) setError(msg); else setSuccess(msg);
    setTimeout(() => { setSuccess(''); setError(''); }, 3500);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const updated = await updateProfile({
        name: form.name.trim() || undefined,
        country: form.country.trim() || undefined,
        bio: form.bio.trim() || undefined,
      });
      setProfile(updated);
      updateUser({ name: updated.name, avatar_url: updated.avatar_url });
      flash('Profile updated successfully.');
    } catch (e) {
      flash(e?.response?.data?.detail || 'Update failed.', true);
    } finally {
      setSaving(false);
    }
  };

  const handleUpload = async (file) => {
    setUploading(true);
    try {
      const res = await uploadAvatar(file);
      setProfile((p) => ({ ...p, avatar_url: res.avatar_url }));
      updateUser({ avatar_url: res.avatar_url });
      flash('Photo updated.');
      getSecurityScore().then(setScore);
    } catch (e) {
      flash(e?.response?.data?.detail || 'Upload failed.', true);
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteAvatar = async () => {
    setUploading(true);
    try {
      await deleteAvatar();
      setProfile((p) => ({ ...p, avatar_url: null }));
      updateUser({ avatar_url: null });
      flash('Photo removed.');
    } catch {
      flash('Failed to remove photo.', true);
    } finally {
      setUploading(false);
    }
  };

  if (loading) {
    return (
      <>
        <Topbar title="Profile" />
        <div className="prof-content"><div className="prof-skeleton" /></div>
      </>
    );
  }

  return (
    <>
      <Topbar title="Profile" />
      <div className="prof-content">

        {success && (
          <div className="prof-toast prof-toast--success">
            <Check size={14} /> {success}
          </div>
        )}
        {error && (
          <div className="prof-toast prof-toast--error">
            <AlertCircle size={14} /> {error}
          </div>
        )}

        <div className="prof-grid">

          {/* Left column */}
          <div className="prof-left">
            <div className="prof-card">
              <AvatarSection
                profile={profile}
                onUpload={handleUpload}
                onDelete={handleDeleteAvatar}
                uploading={uploading}
              />
            </div>

            {/* Account info */}
            <div className="prof-card">
              <h3 className="prof-card-title">Account Info</h3>
              <div className="prof-info-list">
                <div className="prof-info-row">
                  <Mail size={14} />
                  <div>
                    <span className="prof-info-label">Email</span>
                    <span className="prof-info-val">{profile?.email}</span>
                  </div>
                  {profile?.email_verified ? (
                    <span className="prof-badge prof-badge--green">
                      <ShieldCheck size={11} /> Verified
                    </span>
                  ) : (
                    <span className="prof-badge prof-badge--yellow">Unverified</span>
                  )}
                </div>
                <div className="prof-info-row">
                  <Calendar size={14} />
                  <div>
                    <span className="prof-info-label">Member since</span>
                    <span className="prof-info-val">{fmt(profile?.created_at)}</span>
                  </div>
                </div>
              </div>
            </div>

            <SecurityScore data={score} />
          </div>

          {/* Right column — edit form */}
          <div className="prof-right">
            <div className="prof-card">
              <h2 className="prof-section-title">Personal Information</h2>
              <p className="prof-section-sub">Update your name, location, and bio.</p>

              <div className="prof-form">
                <div className="prof-field">
                  <label className="prof-label">Full Name</label>
                  <input
                    className="prof-input"
                    value={form.name}
                    onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))}
                    placeholder="Your full name"
                    maxLength={100}
                  />
                </div>

                <div className="prof-field">
                  <label className="prof-label">Email Address</label>
                  <input
                    className="prof-input prof-input--readonly"
                    value={profile?.email || ''}
                    readOnly
                    title="Email cannot be changed"
                  />
                  <p className="prof-field-hint">
                    Email changes are not supported at this time.
                  </p>
                </div>

                <div className="prof-field">
                  <label className="prof-label">
                    <MapPin size={13} /> Country
                  </label>
                  <input
                    className="prof-input"
                    value={form.country}
                    onChange={(e) => setForm((f) => ({ ...f, country: e.target.value }))}
                    placeholder="e.g. India"
                    maxLength={100}
                  />
                </div>

                <div className="prof-field">
                  <label className="prof-label">
                    <FileText size={13} /> Bio
                  </label>
                  <textarea
                    className="prof-textarea"
                    value={form.bio}
                    onChange={(e) => setForm((f) => ({ ...f, bio: e.target.value }))}
                    placeholder="A short description about yourself…"
                    maxLength={500}
                    rows={3}
                  />
                  <p className="prof-field-hint">{form.bio.length}/500</p>
                </div>

                <button
                  className="prof-save-btn"
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving
                    ? <><Loader size={14} className="spin" /> Saving…</>
                    : <><Save size={14} /> Save Changes</>
                  }
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
