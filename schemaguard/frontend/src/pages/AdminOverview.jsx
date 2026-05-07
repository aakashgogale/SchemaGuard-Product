import { useEffect, useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { adminAPI } from '../api/client';

function Stat({ label, value, subtitle, tone = 'slate' }) {
  const toneClass = tone === 'red' ? 'text-red-600' : tone === 'green' ? 'text-green-600' : 'text-slate-900';
  return (
    <div className="card p-5">
      <p className="text-sm text-slate-500">{label}</p>
      <p className={`mt-2 text-3xl font-bold ${toneClass}`}>{value ?? 0}</p>
      {subtitle && <p className="mt-1 text-xs text-slate-400">{subtitle}</p>}
    </div>
  );
}

export default function AdminOverview() {
  const [stats, setStats] = useState(null);
  useEffect(() => { adminAPI.stats().then(setStats); }, []);
  return (
    <AdminLayout>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Admin Overview</h1>
        <p className="text-sm text-slate-500">Platform-wide health and usage.</p>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        <Stat label="Total Users" value={stats?.total_users} subtitle={`${stats?.new_users_this_week ?? 0} new this week`} />
        <Stat label="Active Today" value={stats?.active_users_today} />
        <Stat label="Total APIs registered" value={stats?.total_registries} />
        <Stat label="Total versions uploaded" value={stats?.total_versions} />
        <Stat label="Breaking changes detected" value={stats?.total_breaking_changes} tone="red" />
        <Stat label="Safe changes" value={stats?.total_safe_changes} tone="green" />
      </div>
      <div className="card mt-6 overflow-hidden">
        <div className="p-5 border-b border-slate-200">
          <h2 className="font-bold text-slate-900">Recently active users</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <tbody className="divide-y divide-slate-100">
              {(stats?.recent_users || []).map((user) => (
                <tr key={user.id}>
                  <td className="p-4 font-medium text-slate-800">{user.email}</td>
                  <td className="p-4 text-slate-500">{user.activity_status}</td>
                  <td className="p-4 text-slate-500">{user.total_uploads} uploads</td>
                  <td className="p-4 text-slate-500">{user.total_registries} APIs</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </AdminLayout>
  );
}
