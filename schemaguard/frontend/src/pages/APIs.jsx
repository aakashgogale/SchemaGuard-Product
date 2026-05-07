import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Database, Eye, Trash2 } from 'lucide-react';
import AppLayout from '../components/AppLayout';
import StatusBadge from '../components/StatusBadge';
import { registryAPI } from '../api/client';
import { fetchRegistriesWithVersions } from '../utils/registryData';

export default function APIs() {
  const [registries, setRegistries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      setRegistries(await fetchRegistriesWithVersions());
    } catch {
      setError('Could not load APIs. Please log in again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const deleteRegistry = async (id) => {
    if (!confirm('Delete this API and all schema versions?')) return;
    await registryAPI.delete(id);
    load();
  };

  return (
    <AppLayout>
      <div className="flex items-start justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">APIs</h1>
          <p className="text-sm text-slate-500 mt-1">Open, inspect, and manage your registered API contracts.</p>
        </div>
        <Link to="/dashboard" className="btn-primary text-sm">Register new API</Link>
      </div>

      <div className="card overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center gap-2">
          <Database className="w-5 h-5 text-indigo-500" />
          <h2 className="font-semibold text-slate-900">Registered APIs</h2>
        </div>
        {error && <div className="p-6 text-red-600">{error}</div>}
        {loading ? (
          <div className="p-6 text-slate-500">Loading APIs...</div>
        ) : registries.length === 0 ? (
          <div className="p-12 text-center">
            <p className="font-semibold text-slate-700">No APIs registered yet</p>
            <p className="text-sm text-slate-400 mt-1">Go to Dashboard and register your first API.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="px-6 py-3 text-left font-semibold text-slate-600">Name</th>
                  <th className="px-6 py-3 text-left font-semibold text-slate-600">Versions</th>
                  <th className="px-6 py-3 text-left font-semibold text-slate-600">Latest</th>
                  <th className="px-6 py-3 text-left font-semibold text-slate-600">Status</th>
                  <th className="px-6 py-3 text-right font-semibold text-slate-600">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {registries.map((registry) => {
                  const latest = registry.versions?.[0];
                  return (
                    <tr key={registry.id} className="hover:bg-slate-50">
                      <td className="px-6 py-4">
                        <p className="font-medium text-slate-900">{registry.name}</p>
                        <p className="text-xs text-slate-400">{registry.description || 'No description'}</p>
                      </td>
                      <td className="px-6 py-4 text-slate-500">{registry.version_count}</td>
                      <td className="px-6 py-4 text-slate-500">{latest ? `v${latest.version}` : '-'}</td>
                      <td className="px-6 py-4"><StatusBadge status={latest ? 'ACTIVE' : 'PENDING'} /></td>
                      <td className="px-6 py-4">
                        <div className="flex justify-end gap-2">
                          <Link to={`/api/${registry.id}`} className="btn-secondary px-3 py-2 text-xs">
                            <Eye className="w-4 h-4 mr-1" /> Open
                          </Link>
                          <button onClick={() => deleteRegistry(registry.id)} className="btn-danger">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AppLayout>
  );
}
