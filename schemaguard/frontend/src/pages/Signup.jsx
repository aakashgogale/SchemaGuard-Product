import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Loader2, ShieldCheck } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

function getPasswordStrength(pw) {
  if (!pw) return { level: '', color: '', width: '0%' };
  let score = 0;
  if (pw.length >= 8) score++;
  if (pw.length >= 12) score++;
  if (/[A-Z]/.test(pw)) score++;
  if (/[0-9]/.test(pw)) score++;
  if (/[^A-Za-z0-9]/.test(pw)) score++;
  if (score <= 2) return { level: 'Weak', color: 'bg-red-500', width: '33%' };
  if (score <= 3) return { level: 'Medium', color: 'bg-amber-500', width: '66%' };
  return { level: 'Strong', color: 'bg-green-500', width: '100%' };
}

export default function Signup() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [errors, setErrors] = useState({});
  const [serverError, setServerError] = useState('');
  const [loading, setLoading] = useState(false);
  const { signup } = useAuth();
  const navigate = useNavigate();

  const strength = getPasswordStrength(password);

  const validateField = (field) => {
    const newErrors = { ...errors };
    if (field === 'email') {
      if (!email) newErrors.email = 'Email is required';
      else if (!/\S+@\S+\.\S+/.test(email)) newErrors.email = 'Enter a valid email';
      else delete newErrors.email;
    }
    if (field === 'password') {
      if (!password) newErrors.password = 'Password is required';
      else if (password.length < 8) newErrors.password = 'Must be at least 8 characters';
      else delete newErrors.password;
    }
    if (field === 'confirmPassword') {
      if (password !== confirmPassword) newErrors.confirmPassword = 'Passwords do not match';
      else delete newErrors.confirmPassword;
    }
    setErrors(newErrors);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    validateField('email');
    validateField('password');
    validateField('confirmPassword');
    if (Object.keys(errors).length > 0 || !email || password.length < 8 || password !== confirmPassword) return;

    setServerError('');
    setLoading(true);
    try {
      await signup(email, password);
      navigate('/dashboard');
    } catch (err) {
      if (!err.response) {
        setServerError('Backend is not running. Start the Flask API on http://localhost:5000 and try again.');
      } else if (err.response.status === 409) {
        setServerError('An account with this email already exists');
      } else if (err.response.status === 422) {
        const detail = err.response.data?.detail?.[0]?.message;
        setServerError(detail || 'Please check the form fields and try again.');
      } else {
        setServerError(err.response.data?.message || 'Something went wrong. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar />
      <div className="flex-1 flex items-center justify-center px-6 py-32">
        <div className="w-full max-w-md animate-fade-in">
          <div className="card p-8">
            <div className="text-center mb-8">
              <div className="w-11 h-11 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-3">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h1 className="text-2xl font-bold text-slate-900">Create your account</h1>
              <p className="text-sm text-slate-500 mt-1">Start detecting breaking changes in minutes</p>
            </div>
            <form onSubmit={handleSubmit} className="space-y-5">
              <div>
                <label htmlFor="signup-email" className="label">Email address</label>
                <input id="signup-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                  onBlur={() => validateField('email')} placeholder="you@company.com"
                  className={`input-field ${errors.email ? 'border-red-400 focus:ring-red-500' : ''}`} required />
                {errors.email && <p className="error-text">{errors.email}</p>}
              </div>
              <div>
                <label htmlFor="signup-password" className="label">Password</label>
                <input id="signup-password" type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                  onBlur={() => validateField('password')} placeholder="Minimum 8 characters"
                  className={`input-field ${errors.password ? 'border-red-400 focus:ring-red-500' : ''}`} required />
                {errors.password && <p className="error-text">{errors.password}</p>}
                {password && (
                  <div className="mt-2">
                    <div className="h-1.5 bg-slate-200 rounded-full overflow-hidden">
                      <div className={`h-full ${strength.color} transition-all duration-300 rounded-full`} style={{ width: strength.width }} />
                    </div>
                    <p className={`text-xs mt-1 font-medium ${strength.level === 'Weak' ? 'text-red-500' : strength.level === 'Medium' ? 'text-amber-500' : 'text-green-500'}`}>
                      {strength.level}
                    </p>
                  </div>
                )}
              </div>
              <div>
                <label htmlFor="signup-confirm" className="label">Confirm password</label>
                <input id="signup-confirm" type="password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)}
                  onBlur={() => validateField('confirmPassword')} placeholder="Re-enter your password"
                  className={`input-field ${errors.confirmPassword ? 'border-red-400 focus:ring-red-500' : ''}`} required />
                {errors.confirmPassword && <p className="error-text">{errors.confirmPassword}</p>}
              </div>
              {serverError && <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-600">{serverError}</div>}
              <button type="submit" className="btn-primary w-full py-3" disabled={loading}>
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <Loader2 className="animate-spin w-4 h-4" />
                    Creating account...
                  </span>
                ) : 'Create account'}
              </button>
            </form>
            <p className="text-center text-sm text-slate-500 mt-6">
              Already have an account?{' '}<Link to="/login" className="text-indigo-500 hover:text-indigo-600 font-medium">Sign in</Link>
            </p>
          </div>
        </div>
      </div>
      <Footer variant="full" />
    </div>
  );
}
