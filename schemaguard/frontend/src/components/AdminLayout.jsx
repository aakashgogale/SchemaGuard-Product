import { Link, NavLink } from 'react-router-dom';
import { BarChart3, Database, Settings, ShieldCheck, Users } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';

const links = [
  { to: '/admin', label: 'Overview', icon: BarChart3 },
  { to: '/admin/users', label: 'Users', icon: Users },
  { to: '/admin/apis', label: 'APIs', icon: Database },
  { to: '/admin/settings', label: 'Settings', icon: Settings },
];

export default function AdminLayout({ children }) {
  const { user } = useAuth();
  return (
    <div className="min-h-screen bg-slate-50 flex">
      <aside className="hidden lg:flex w-64 bg-slate-950 text-white flex-col">
        <div className="h-16 px-6 flex items-center gap-2 border-b border-slate-800">
          <ShieldCheck className="w-5 h-5 text-amber-300" />
          <span className="font-bold">SchemaGuard Admin</span>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {links.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/admin'}
                className={({ isActive }) =>
                  `flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all ${
                    isActive ? 'bg-amber-400/10 text-amber-200 border-l-2 border-amber-300' : 'text-slate-400 hover:bg-slate-900 hover:text-white'
                  }`
                }
              >
                <Icon className="w-5 h-5" />
                {item.label}
              </NavLink>
            );
          })}
        </nav>
        <div className="p-4 border-t border-slate-800 text-sm text-slate-400">
          <p className="truncate">{user?.email}</p>
          <Link to="/dashboard" className="mt-3 inline-block text-amber-200 hover:text-amber-100">Back to app</Link>
        </div>
      </aside>
      <main className="flex-1 min-w-0 p-5 lg:p-8">{children}</main>
    </div>
  );
}
