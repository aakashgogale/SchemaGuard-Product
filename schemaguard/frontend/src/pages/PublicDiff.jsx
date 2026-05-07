import { useEffect, useMemo, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';
import { publicAPI } from '../api/client';
import StatusBadge from '../components/StatusBadge';

export default function PublicDiff() {
  const { token } = useParams();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function load() {
      try {
        setData(await publicAPI.getDiff(token));
      } catch {
        setError('This diff link is invalid or has expired.');
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [token]);

  const changes = data?.diff_result?.changes || [];
  const sortedChanges = useMemo(() => {
    return [...changes].sort((a, b) => {
      if (a.change_type === b.change_type) return 0;
      return a.change_type === 'BREAKING' ? -1 : 1;
    });
  }, [changes]);
  const breakingCount = data?.diff_result?.breaking_count || 0;
  const safeCount = data?.diff_result?.safe_count || 0;
  const isBreaking = Boolean(data?.diff_result?.is_breaking);

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 font-bold text-slate-900">
            <ShieldCheck className="w-5 h-5 text-indigo-500" />
            SchemaGuard
          </Link>
          <Link to="/signup" className="btn-primary py-2 px-4 text-sm">Create free account</Link>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-10">
        {loading ? (
          <div className="space-y-4 animate-pulse">
            <div className="skeleton h-8 w-72" />
            <div className="skeleton h-4 w-96" />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4"><div className="skeleton h-28" /><div className="skeleton h-28" /><div className="skeleton h-28" /></div>
          </div>
        ) : error ? (
          <div className="card p-10 text-center">
            <h1 className="text-2xl font-bold text-slate-900 mb-2">Invalid diff link</h1>
            <p className="text-slate-500">{error}</p>
          </div>
        ) : (
          <>
            <div className="mb-8">
              <h1 className="text-3xl font-bold text-slate-900">{data.registry_name} - {data.version}</h1>
              <p className="text-sm text-slate-500 mt-2">Uploaded {new Date(data.uploaded_at).toLocaleString()}</p>
              {data.change_reason && (
                <p className="mt-4 rounded-lg border border-indigo-100 bg-indigo-50 p-4 text-sm text-indigo-900">
                  <strong>Change reason:</strong> {data.change_reason}
                </p>
              )}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              <div className="card p-5"><p className="text-sm text-slate-500 mb-2">Status</p><StatusBadge status={isBreaking ? 'BREAKING' : 'SAFE'} /></div>
              <div className="card p-5"><p className="text-sm text-slate-500">Breaking changes</p><p className="text-3xl font-bold text-red-600">{breakingCount}</p></div>
              <div className="card p-5"><p className="text-sm text-slate-500">Safe changes</p><p className="text-3xl font-bold text-green-600">{safeCount}</p></div>
            </div>

            <div className="card overflow-hidden mb-8">
              <div className="px-5 py-4 border-b border-slate-200">
                <h2 className="font-semibold text-slate-900">Full changes list</h2>
              </div>
              <div className="divide-y divide-slate-100">
                {sortedChanges.length === 0 ? (
                  <p className="p-5 text-sm text-slate-500">No changes detected.</p>
                ) : sortedChanges.map((change, index) => (
                  <div key={`${change.path}-${index}`} className="p-5">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <StatusBadge status={change.change_type} />
                      <code className="text-sm text-slate-800">{change.path}</code>
                    </div>
                    <p className="text-sm text-slate-500">{change.reason}</p>
                  </div>
                ))}
              </div>
            </div>

            <section className="rounded-xl bg-slate-900 p-8 text-center">
              <h2 className="text-2xl font-bold text-white mb-2">Register your own APIs on SchemaGuard - Free to use</h2>
              <p className="text-slate-400 mb-6">Catch breaking schema changes before your consumers do.</p>
              <Link to="/signup" className="btn-primary">Start free</Link>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
