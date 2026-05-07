import { useEffect, useMemo, useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { adminAPI } from '../api/client';

const tabs = ['all', 'online', 'away', 'inactive', 'suspended'];

function StatusBadge({ status }) {
  const classes = {
    online: 'bg-green-50 text-green-700',
    away: 'bg-amber-50 text-amber-700',
    inactive: 'bg-slate-100 text-slate-600',
    suspended: 'bg-red-50 text-red-700',
    never: 'bg-slate-100 text-slate-500',
  };
  return <span className={`rounded-full px-2 py-1 text-xs font-semibold ${classes[status] || classes.inactive}`}>{status}</span>;
}

export default function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [query, setQuery] = useState('');
  const [tab, setTab] = useState('all');
  const load = () => adminAPI.users().then((data) => setUsers(data.users || []));
  useEffect(() => { load(); }, []);
  const filtered = useMemo(() => users.filter((user) => {
    const status = user.is_active ? user.activity_status : 'suspended';
    return user.email.toLowerCase().includes(query.toLowerCase()) && (tab === 'all' || status === tab);
  }), [users, query, tab]);
  return (
    <AdminLayout>
      <h1 className="text-2xl font-bold text-slate-900 mb-4">Users</h1>
      <div className="card p-4 mb-4 flex flex-col gap-3">
        <input className="input-field" placeholder="Search by email" value={query} onChange={(event) => setQuery(event.target.value)} />
        <div className="flex flex-wrap gap-2">
          {tabs.map((item) => (
            <button key={item} onClick={() => setTab(item)} className={`rounded-lg px-3 py-1.5 text-sm font-semibold ${tab === item ? 'bg-indigo-500 text-white' : 'bg-slate-100 text-slate-600'}`}>{item}</button>
          ))}
        </div>
      </div>
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-500">
            <tr>
              <th className="p-4">Avatar+Email</th>
              <th className="p-4">Status</th>
              <th className="p-4">Last Active</th>
              <th className="p-4">Uploads</th>
              <th className="p-4">APIs owned</th>
              <th className="p-4">Admin</th>
              <th className="p-4">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filtered.map((user) => (
              <tr key={user.id}>
                <td className="p-4 font-medium text-slate-800">{user.email}</td>
                <td className="p-4"><StatusBadge status={user.is_active ? user.activity_status : 'suspended'} /></td>
                <td className="p-4 text-slate-500">{user.last_active_at ? new Date(user.last_active_at).toLocaleString() : 'Never'}</td>
                <td className="p-4">{user.total_uploads}</td>
                <td className="p-4">{user.total_registries}</td>
                <td className="p-4">{user.is_admin && <span className="rounded-full bg-amber-50 px-2 py-1 text-xs font-semibold text-amber-700">Admin</span>}</td>
                <td className="p-4 flex gap-2">
                  <button onClick={() => adminAPI.toggleUser(user.id).then(load)} className="btn-secondary">{user.is_active ? 'Suspend' : 'Reactivate'}</button>
                  {!user.is_admin && <button onClick={() => adminAPI.makeAdmin(user.id).then(load)} className="btn-primary">Make Admin</button>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AdminLayout>
  );
}
