import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { AlertTriangle, CheckCircle2, GitBranch, Inbox, Package, Plus } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { registryAPI } from '../api/client';
import Sidebar from '../components/Sidebar';
import Footer from '../components/Footer';
import StatusBadge from '../components/StatusBadge';
import { fetchRegistriesWithVersions } from '../utils/registryData';

function StatCard({ label, value, color, icon }) {
  return (
    <div className="card p-5">
      <div className="flex items-center justify-between mb-3">
        <span className="text-sm font-medium text-slate-500">{label}</span>
        <span className={`w-9 h-9 rounded-lg flex items-center justify-center ${color}`}>{icon}</span>
      </div>
      <p className="text-2xl font-bold text-slate-900">{value}</p>
    </div>
  );
}

function SkeletonRow() {
  return (
    <tr className="animate-pulse">
      <td className="px-6 py-4"><div className="skeleton h-4 w-32" /></td>
      <td className="px-6 py-4"><div className="skeleton h-4 w-16" /></td>
      <td className="px-6 py-4"><div className="skeleton h-5 w-20 rounded-full" /></td>
      <td className="px-6 py-4"><div className="skeleton h-4 w-24" /></td>
      <td className="px-6 py-4"><div className="skeleton h-4 w-20" /></td>
    </tr>
  );
}

function slugifyName(value) {
  return value
    .trim()
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9_-]/g, '-')
    .replace(/-+/g, '-')
    .replace(/^[-_]+|[-_]+$/g, '');
}

export default function Dashboard() {
  const { user } = useAuth();
  const [registries, setRegistries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [creating, setCreating] = useState(false);
  const [createError, setCreateError] = useState('');

  const fetchRegistries = async () => {
    try {
      setRegistries(await fetchRegistriesWithVersions());
    } catch {
      /* handled by interceptor */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRegistries(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    setCreateError('');
    const normalizedName = slugifyName(newName);
    if (!normalizedName) {
      setCreateError('API name must contain at least one lowercase letter or number.');
      return;
    }
    setCreating(true);
    try {
      await registryAPI.create({ name: normalizedName, description: newDesc.trim() || null });
      setShowModal(false);
      setNewName('');
      setNewDesc('');
      fetchRegistries();
    } catch (err) {
      const detail = err.response?.data?.detail?.[0]?.message;
      setCreateError(detail || err.response?.data?.message || 'Failed to create registry');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Delete this registry and all its versions?')) return;
    try {
      await registryAPI.delete(id);
      fetchRegistries();
    } catch {
      /* no-op */
    }
  };

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';
  const totalVersions = registries.reduce((sum, registry) => sum + (registry.version_count || 0), 0);
  const allVersions = registries.flatMap((registry) => registry.versions || []);
  const breakingChanges = allVersions.reduce(
    (sum, version) => sum + (version.diff_result?.breaking_count || 0),
    0
  );
  const safeChanges = allVersions.reduce(
    (sum, version) => sum + (version.diff_result?.safe_count || 0),
    0
  );

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex-1 flex flex-col min-h-screen">
        <main className="flex-1 p-6 lg:p-10 pt-20 lg:pt-10">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">{greeting}, {user?.username || user?.email?.split('@')[0] || 'there'}</h1>
              <p className="text-sm text-slate-500 mt-1">Here's what's happening with your APIs</p>
            </div>
            <button onClick={() => setShowModal(true)} className="btn-primary text-sm">
              <Plus className="w-4 h-4 mr-2" />
              Register new API
            </button>
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <StatCard label="Total APIs registered" value={registries.length} color="bg-indigo-50 text-indigo-600" icon={<Package className="w-5 h-5" />} />
            <StatCard label="Total versions uploaded" value={totalVersions} color="bg-blue-50 text-blue-600" icon={<GitBranch className="w-5 h-5" />} />
            <StatCard label="Breaking changes detected" value={breakingChanges} color="bg-red-50 text-red-600" icon={<AlertTriangle className="w-5 h-5" />} />
            <StatCard label="Safe changes" value={safeChanges} color="bg-green-50 text-green-600" icon={<CheckCircle2 className="w-5 h-5" />} />
          </div>

          <div className="card overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-200">
              <h2 className="text-base font-semibold text-slate-900">Your APIs</h2>
            </div>
            {loading ? (
              <table className="w-full"><tbody><SkeletonRow /><SkeletonRow /><SkeletonRow /></tbody></table>
            ) : registries.length === 0 ? (
              <div className="py-16 text-center">
                <Inbox className="w-14 h-14 mx-auto mb-4 text-slate-300" />
                <h3 className="text-lg font-semibold text-slate-700 mb-1">No APIs yet</h3>
                <p className="text-sm text-slate-400 mb-6">Register your first API to start tracking schema changes.</p>
                <button onClick={() => setShowModal(true)} className="btn-primary text-sm">Register your first API</button>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-slate-200 bg-slate-50">
                      <th className="px-6 py-3 text-left font-semibold text-slate-600">Name</th>
                      <th className="px-6 py-3 text-left font-semibold text-slate-600">Latest Version</th>
                      <th className="px-6 py-3 text-left font-semibold text-slate-600">Status</th>
                      <th className="px-6 py-3 text-left font-semibold text-slate-600">Last Updated</th>
                      <th className="px-6 py-3 text-right font-semibold text-slate-600">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {registries.map((registry) => {
                      const latestVersion = registry.versions?.[0];
                      const lastUpdated = latestVersion?.uploaded_at || registry.created_at;
                      return (
                        <tr key={registry.id} className="hover:bg-slate-50/80 transition-colors">
                          <td className="px-6 py-4 font-medium text-slate-900">{registry.name}</td>
                          <td className="px-6 py-4 text-slate-500">{latestVersion ? `v${latestVersion.version}` : '-'}</td>
                          <td className="px-6 py-4"><StatusBadge status={registry.version_count > 0 ? 'ACTIVE' : 'PENDING'} /></td>
                          <td className="px-6 py-4 text-slate-500">{new Date(lastUpdated).toLocaleDateString()}</td>
                          <td className="px-6 py-4 text-right space-x-2">
                            <Link to={`/api/${registry.id}`} className="text-indigo-500 hover:text-indigo-600 font-medium text-sm">View</Link>
                            <button onClick={() => handleDelete(registry.id)} className="text-red-400 hover:text-red-600 font-medium text-sm">Delete</button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </main>
        <Footer variant="minimal" />
      </div>

      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setShowModal(false)} />
          <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 animate-fade-in">
            <h2 className="text-lg font-bold text-slate-900 mb-1">Register new API</h2>
            <p className="text-sm text-slate-500 mb-6">Create a registry to start tracking schema versions.</p>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <label htmlFor="reg-name" className="label">API name</label>
                <input id="reg-name" value={newName} onChange={(e) => setNewName(e.target.value)}
                  placeholder="my-api" className="input-field font-mono" required />
                <p className="text-xs text-slate-400 mt-1">
                  Will be saved as: <span className="font-mono">{slugifyName(newName) || 'my-api'}</span>
                </p>
              </div>
              <div>
                <label htmlFor="reg-desc" className="label">Description (optional)</label>
                <textarea id="reg-desc" value={newDesc} onChange={(e) => setNewDesc(e.target.value)}
                  placeholder="What does this API do?" rows={3} className="input-field" />
              </div>
              {createError && <p className="error-text">{createError}</p>}
              <div className="flex justify-end gap-3 pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary text-sm px-4 py-2">Cancel</button>
                <button type="submit" className="btn-primary text-sm px-4 py-2" disabled={creating}>
                  {creating ? 'Creating...' : 'Create registry'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
