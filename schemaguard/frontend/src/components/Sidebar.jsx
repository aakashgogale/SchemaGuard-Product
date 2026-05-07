import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Bot, Database, FileClock, Home, LogOut, Menu, Shield, ShieldCheck, UserCircle } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

const navItems = [
  {
    label: 'Dashboard',
    path: '/dashboard',
    icon: Home,
  },
  {
    label: 'APIs',
    path: '/apis',
    icon: Database,
  },
  {
    label: 'Diff History',
    path: '/diff-history',
    icon: FileClock,
  },
  {
    label: 'AI Agent',
    path: '/ai-agent',
    icon: Bot,
  },
  {
    label: 'Profile',
    path: '/profile',
    icon: UserCircle,
  },
];

export default function Sidebar() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const { user, logout } = useAuth();

  const sidebarContent = (
    <div className="flex flex-col h-full bg-slate-900">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-slate-800">
        <Link to="/dashboard" className="flex items-center gap-2 text-white font-bold text-lg">
          <ShieldCheck className="w-5 h-5 text-indigo-400" />
          <span>SchemaGuard</span>
        </Link>
      </div>

      {/* Nav items */}
      <nav className="flex-1 py-4 px-3 space-y-1">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path ||
            (item.path === '/apis' && location.pathname.startsWith('/api/')) ||
            (item.path === '/diff-history' && location.pathname.startsWith('/diff/'));
          const Icon = item.icon;
          return (
            <Link
              key={item.label}
              to={item.path}
              onClick={() => setMobileOpen(false)}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200
                ${
                  isActive
                    ? 'bg-slate-800 text-white border-l-2 border-indigo-500 ml-0'
                    : 'text-slate-400 hover:bg-slate-800/60 hover:text-slate-200'
                }`}
            >
              <Icon className="w-5 h-5" />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* User section */}
      <div className="p-4 border-t border-slate-800">
        {user?.is_admin && (
          <Link
            to="/admin"
            onClick={() => setMobileOpen(false)}
            className="mb-3 flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-amber-300 hover:bg-slate-800 hover:text-amber-200 transition-all"
          >
            <Shield className="w-4 h-4" />
            Admin Panel
          </Link>
        )}
        <div className="flex items-center gap-3 mb-3">
          <div className="w-8 h-8 rounded-full bg-indigo-500/20 flex items-center justify-center">
            <span className="text-sm font-semibold text-indigo-400">
              {(user?.username || user?.email)?.charAt(0)?.toUpperCase() || 'U'}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <Link to="/profile" onClick={() => setMobileOpen(false)} className="text-sm text-slate-300 truncate block hover:text-white">
              {user?.username || user?.email || 'user'}
            </Link>
            {user?.username && <p className="text-xs text-slate-500 truncate">{user.email}</p>}
          </div>
        </div>
        <button
          onClick={logout}
          className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-slate-400
                     hover:bg-slate-800 hover:text-red-400 transition-all duration-200"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden lg:flex lg:flex-shrink-0">
        <div className="w-60 h-screen sticky top-0">{sidebarContent}</div>
      </aside>

      {/* Mobile toggle */}
      <button
        onClick={() => setMobileOpen(true)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-slate-900 text-white rounded-lg shadow-lg hover:bg-slate-800 transition-colors"
        aria-label="Open sidebar"
      >
        <Menu className="w-5 h-5" />
      </button>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div
            className="absolute inset-0 bg-black/50 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
          />
          <div className="absolute left-0 top-0 h-full w-60 animate-slide-in-right">
            {sidebarContent}
          </div>
        </div>
      )}
    </>
  );
}
