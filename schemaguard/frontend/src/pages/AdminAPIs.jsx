import { useEffect, useMemo, useState } from 'react';
import AdminLayout from '../components/AdminLayout';
import { adminAPI } from '../api/client';

export default function AdminAPIs() {
  const [registries, setRegistries] = useState([]);
  const [query, setQuery] = useState('');
  useEffect(() => { adminAPI.registries().then((data) => setRegistries(data.registries || [])); }, []);
  const filtered = useMemo(() => registries.filter((item) =>
    `${item.name} ${item.owner_email}`.toLowerCase().includes(query.toLowerCase())
  ), [registries, query]);
  return (
    <AdminLayout>
      <h1 className="text-2xl font-bold text-slate-900 mb-4">APIs</h1>
      <div className="card p-4 mb-4">
        <input className="input-field" placeholder="Search by API name or owner email" value={query} onChange={(event) => setQuery(event.target.value)} />
      </div>
      <div className="card overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-slate-50 text-left text-slate-500">
            <tr>
              <th className="p-4">API Name</th>
              <th className="p-4">Owner email</th>
              <th className="p-4">Versions</th>
              <th className="p-4">Breaking changes</th>
              <th className="p-4">Last updated</th>
              <th className="p-4">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {filtered.map((item) => (
              <tr key={item.id}>
                <td className="p-4 font-semibold text-slate-800">{item.name}</td>
                <td className="p-4 text-slate-500">{item.owner_email}</td>
                <td className="p-4">{item.version_count}</td>
                <td className="p-4 text-red-600 font-semibold">{item.breaking_changes_count}</td>
                <td className="p-4 text-slate-500">{item.last_version_uploaded_at ? new Date(item.last_version_uploaded_at).toLocaleString() : 'No uploads'}</td>
                <td className="p-4"><a className="text-indigo-600 font-semibold" href={`/api/${item.id}`}>View Details</a></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AdminLayout>
  );
}
