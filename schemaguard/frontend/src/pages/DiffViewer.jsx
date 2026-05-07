import { useState, useEffect } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
import { ArrowLeft } from 'lucide-react';
import { diffAPI, registryAPI } from '../api/client';
import Sidebar from '../components/Sidebar';
import Footer from '../components/Footer';
import DiffPanel from '../components/DiffPanel';

export default function DiffViewer() {
  const { registryId } = useParams();
  const [searchParams] = useSearchParams();
  const fromId = searchParams.get('from');
  const toId = searchParams.get('to');

  const [diffResult, setDiffResult] = useState(null);
  const [registry, setRegistry] = useState(null);
  const [fromVersion, setFromVersion] = useState(null);
  const [toVersion, setToVersion] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [diff, reg] = await Promise.all([
          fromId && toId ? diffAPI.compare(registryId, fromId, toId) : null,
          registryAPI.get(registryId),
        ]);
        const versions = reg?.versions || [];
        setDiffResult(diff);
        setRegistry(reg);
        setFromVersion(versions.find((version) => version.id === fromId) || null);
        setToVersion(versions.find((version) => version.id === toId) || null);
      } catch {
        setError('Failed to load diff results');
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [registryId, fromId, toId]);

  const heading = fromVersion && toVersion
    ? `Comparing v${fromVersion.version} -> v${toVersion.version}`
    : 'Schema Comparison';

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex-1 flex flex-col min-h-screen">
        <main className="flex-1 p-6 lg:p-10 pt-20 lg:pt-10">
          <Link to={`/api/${registryId}`} className="text-sm text-indigo-500 hover:text-indigo-600 font-medium mb-6 inline-flex items-center gap-1">
            <ArrowLeft className="w-4 h-4" />
            Back to API
          </Link>

          {loading ? (
            <div className="animate-pulse space-y-4 mt-6">
              <div className="skeleton h-8 w-64" />
              <div className="skeleton h-4 w-40" />
              <div className="skeleton h-64 w-full rounded-xl mt-6" />
            </div>
          ) : error ? (
            <div className="card p-8 text-center mt-6">
              <p className="text-red-500">{error}</p>
            </div>
          ) : (
            <div className="mt-6">
              <h1 className="text-2xl font-bold text-slate-900 mb-2">
                {registry?.name ? `${registry.name} - ` : ''}{heading}
              </h1>
              {diffResult && (
                <div className="flex flex-wrap items-center gap-3 mb-8">
                  <span className="px-3 py-1.5 rounded-full text-xs font-semibold bg-red-50 text-red-700 border border-red-200">
                    {diffResult.breaking_count} breaking
                  </span>
                  <span className="px-3 py-1.5 rounded-full text-xs font-semibold bg-green-50 text-green-700 border border-green-200">
                    {diffResult.safe_count} safe
                  </span>
                  <span className="text-sm text-slate-500">
                    {diffResult.total_changes} total changes
                  </span>
                </div>
              )}
              {diffResult ? (
                <DiffPanel
                  changes={diffResult.changes || []}
                  v1Schema={fromVersion?.schema_json || {}}
                  v2Schema={toVersion?.schema_json || {}}
                />
              ) : (
                <div className="card p-8 text-center">
                  <p className="text-slate-500">No diff data available. Please provide both from and to version IDs.</p>
                </div>
              )}
            </div>
          )}
        </main>
        <Footer variant="minimal" />
      </div>
    </div>
  );
}
