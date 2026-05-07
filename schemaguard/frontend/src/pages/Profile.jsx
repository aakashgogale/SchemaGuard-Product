import { useEffect, useState } from 'react';
import { KeyRound, Mail, UserCircle } from 'lucide-react';
import AppLayout from '../components/AppLayout';
import { authAPI, profileAPI } from '../api/client';
import { useAuth } from '../hooks/useAuth';

export default function Profile() {
  const { user } = useAuth();
  const [username, setUsername] = useState(user?.username || user?.email?.split('@')[0] || '');
  const [email, setEmail] = useState(user?.email || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [resetEmail, setResetEmail] = useState(user?.email || '');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    async function loadProfile() {
      try {
        const profile = await profileAPI.get();
        setUsername(profile.username || profile.email.split('@')[0]);
        setEmail(profile.email);
        setResetEmail(profile.email);
      } catch {
        setError('Could not load profile.');
      }
    }
    loadProfile();
  }, []);

  const showSuccess = (text) => {
    setError('');
    setMessage(text);
  };

  const showError = (err, fallback) => {
    setMessage('');
    setError(err.response?.data?.message || err.response?.data?.detail?.[0]?.message || fallback);
  };

  const updateEmail = async (event) => {
    event.preventDefault();
    setSaving(true);
    try {
      const profile = await profileAPI.updateEmail({ email });
      localStorage.setItem('schemaguard_user', JSON.stringify({ id: profile.id, email: profile.email, username: profile.username, is_admin: profile.is_admin }));
      showSuccess('Email updated. Refresh or log in again to update every screen.');
    } catch (err) {
      showError(err, 'Could not update email.');
    } finally {
      setSaving(false);
    }
  };

  const updateUsername = async (event) => {
    event.preventDefault();
    setSaving(true);
    try {
      const profile = await profileAPI.updateUsername({ username });
      localStorage.setItem('schemaguard_user', JSON.stringify({ id: profile.id, email: profile.email, username: profile.username, is_admin: profile.is_admin }));
      showSuccess('Username updated successfully.');
    } catch (err) {
      showError(err, 'Could not update username.');
    } finally {
      setSaving(false);
    }
  };

  const updatePassword = async (event) => {
    event.preventDefault();
    setSaving(true);
    try {
      await profileAPI.updatePassword({ current_password: currentPassword, new_password: newPassword });
      setCurrentPassword('');
      setNewPassword('');
      showSuccess('Password updated successfully.');
    } catch (err) {
      showError(err, 'Could not update password.');
    } finally {
      setSaving(false);
    }
  };

  const forgotPassword = async (event) => {
    event.preventDefault();
    setSaving(true);
    try {
      await authAPI.forgotPassword({ email: resetEmail });
      showSuccess('Reset request accepted. In production this would send an email.');
    } catch (err) {
      showError(err, 'Could not process reset request.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <AppLayout>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Profile</h1>
        <p className="text-sm text-slate-500 mt-1">Manage username, email, password, and reset flow.</p>
      </div>

      {(message || error) && (
        <div className={`mb-6 rounded-lg border p-4 text-sm ${message ? 'bg-green-50 border-green-200 text-green-700' : 'bg-red-50 border-red-200 text-red-700'}`}>
          {message || error}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <form onSubmit={updateUsername} className="card p-6">
          <UserCircle className="w-6 h-6 text-indigo-500 mb-4" />
          <h2 className="font-bold text-slate-900 mb-4">Username</h2>
          <label className="label" htmlFor="profile-username">Display username</label>
          <input id="profile-username" className="input-field" type="text" minLength={2} maxLength={100} value={username} onChange={(e) => setUsername(e.target.value)} />
          <button className="btn-primary mt-4 w-full" disabled={saving || username.trim().length < 2}>Update username</button>
        </form>

        <form onSubmit={updateEmail} className="card p-6">
          <Mail className="w-6 h-6 text-indigo-500 mb-4" />
          <h2 className="font-bold text-slate-900 mb-4">Email</h2>
          <label className="label" htmlFor="profile-email">Email address</label>
          <input id="profile-email" className="input-field" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <button className="btn-primary mt-4 w-full" disabled={saving}>Update email</button>
        </form>

        <form onSubmit={updatePassword} className="card p-6">
          <KeyRound className="w-6 h-6 text-indigo-500 mb-4" />
          <h2 className="font-bold text-slate-900 mb-4">Password</h2>
          <label className="label" htmlFor="current-password">Current password</label>
          <input id="current-password" className="input-field mb-3" type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
          <label className="label" htmlFor="new-password">New password</label>
          <input id="new-password" className="input-field" type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
          <button className="btn-primary mt-4 w-full" disabled={saving || newPassword.length < 8}>Change password</button>
        </form>

        <form onSubmit={forgotPassword} className="card p-6">
          <UserCircle className="w-6 h-6 text-indigo-500 mb-4" />
          <h2 className="font-bold text-slate-900 mb-4">Forgot password</h2>
          <label className="label" htmlFor="reset-email">Recovery email</label>
          <input id="reset-email" className="input-field" type="email" value={resetEmail} onChange={(e) => setResetEmail(e.target.value)} />
          <button className="btn-secondary mt-4 w-full" disabled={saving}>Request reset</button>
          <p className="text-xs text-slate-400 mt-3">This assessment build simulates the reset request.</p>
        </form>
      </div>
    </AppLayout>
  );
}
