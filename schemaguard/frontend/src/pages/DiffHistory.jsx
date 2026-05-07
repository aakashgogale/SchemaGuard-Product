import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { GitCompare } from 'lucide-react';
import AppLayout from '../components/AppLayout';
import StatusBadge from '../components/StatusBadge';
import { fetchRegistriesWithVersions, flattenDiffs } from '../utils/registryData';

export default function DiffHistory() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const registries = await fetchRegistriesWithVersions();
        setItems(flattenDiffs(registries));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <AppLayout>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Diff History</h1>
        <p className="text-sm text-slate-500 mt-1">Every analyzed schema upload in one place.</p>
      </div>

      <div className="card overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex items-center gap-2">
          <GitCompare className="w-5 h-5 text-indigo-500" />
          <h2 className="font-semibold text-slate-900">Analyzed changes</h2>
        </div>
        {loading ? (
          <div className="p-6 text-slate-500">Loading diff history...</div>
        ) : items.length === 0 ? (
          <div className="p-12 text-center">
            <p className="font-semibold text-slate-700">No diffs yet</p>
            <p className="text-sm text-slate-400 mt-1">Upload at least two schema versions for an API.</p>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {items.map(({ registry, version, diff }) => (
              <div key={version.id} className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-slate-50">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <p className="font-semibold text-slate-900">{registry.name} v{version.version}</p>
                    <StatusBadge status={diff.is_breaking ? 'BREAKING' : 'SAFE'} />
                  </div>
                  <p className="text-sm text-slate-500">
                    {diff.breaking_count} breaking, {diff.safe_count} safe, {diff.total_changes} total changes
                  </p>
                </div>
                <Link to={`/api/${registry.id}`} className="btn-secondary text-sm px-4 py-2">Open API</Link>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppLayout>
  );
}
