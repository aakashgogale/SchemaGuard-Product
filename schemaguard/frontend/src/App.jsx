import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './hooks/useAuth';

import Landing from './pages/Landing';
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import APIs from './pages/APIs';
import APIDetail from './pages/APIDetail';
import DiffViewer from './pages/DiffViewer';
import DiffHistory from './pages/DiffHistory';
import Profile from './pages/Profile';
import AIAgent from './pages/AIAgent';
import PublicDiff from './pages/PublicDiff';
import PublicConversation from './pages/PublicConversation';
import AdminOverview from './pages/AdminOverview';
import AdminUsers from './pages/AdminUsers';
import AdminAPIs from './pages/AdminAPIs';
import AdminSettings from './pages/AdminSettings';
import ProtectedRoute from './components/ProtectedRoute';
import AdminRoute from './components/AdminRoute';

function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50">
      <div className="text-center animate-fade-in">
        <div className="text-8xl font-black text-slate-200 mb-4">404</div>
        <h1 className="text-2xl font-bold text-slate-900 mb-2">Page not found</h1>
        <p className="text-slate-500 mb-8">
          The page you're looking for doesn't exist or has been moved.
        </p>
        <a href="/" className="btn-primary">Go home</a>
      </div>
    </div>
  );
}

function PublicRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return null;
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/public/diff/:token" element={<PublicDiff />} />
      <Route path="/public/conversation/:token" element={<PublicConversation />} />
      <Route
        path="/login"
        element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        }
      />
      <Route
        path="/signup"
        element={
          <PublicRoute>
            <Signup />
          </PublicRoute>
        }
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/apis"
        element={
          <ProtectedRoute>
            <APIs />
          </ProtectedRoute>
        }
      />
      <Route
        path="/api/:id"
        element={
          <ProtectedRoute>
            <APIDetail />
          </ProtectedRoute>
        }
      />
      <Route
        path="/diff-history"
        element={
          <ProtectedRoute>
            <DiffHistory />
          </ProtectedRoute>
        }
      />
      <Route
        path="/diff/:registryId"
        element={
          <ProtectedRoute>
            <DiffViewer />
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <Profile />
          </ProtectedRoute>
        }
      />
      <Route
        path="/ai-agent"
        element={
          <ProtectedRoute>
            <AIAgent />
          </ProtectedRoute>
        }
      />
      <Route path="/admin" element={<AdminRoute><AdminOverview /></AdminRoute>} />
      <Route path="/admin/users" element={<AdminRoute><AdminUsers /></AdminRoute>} />
      <Route path="/admin/apis" element={<AdminRoute><AdminAPIs /></AdminRoute>} />
      <Route path="/admin/settings" element={<AdminRoute><AdminSettings /></AdminRoute>} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
