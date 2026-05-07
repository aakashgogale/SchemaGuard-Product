import StatusBadge from './StatusBadge';
import { Clock } from 'lucide-react';

function formatDate(dateStr) {
  return new Date(dateStr).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function VersionTimeline({ versions = [], selectedId, onSelect }) {
  if (versions.length === 0) {
    return (
      <div className="text-center py-12 text-slate-400">
        <Clock className="w-12 h-12 mx-auto mb-3 text-slate-300" />
        <p className="text-sm font-medium">No versions yet</p>
        <p className="text-xs mt-1">Upload your first schema version</p>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Connecting line */}
      <div className="absolute left-4 top-6 bottom-6 w-0.5 bg-slate-200" />

      <div className="space-y-3">
        {versions.map((version, idx) => {
          const isSelected = version.id === selectedId;
          const isLatest = idx === 0;
          const diffResult = version.diff_result;
          const breakingCount = diffResult?.breaking_count || 0;
          const safeCount = diffResult?.safe_count || 0;

          return (
            <button
              key={version.id}
              onClick={() => onSelect(version.id)}
              className={`relative w-full text-left pl-10 pr-4 py-3 rounded-xl border transition-all duration-200
                ${
                  isSelected
                    ? 'bg-white border-indigo-300 ring-2 ring-indigo-500/20 shadow-sm'
                    : 'bg-white border-slate-200 hover:border-slate-300 hover:shadow-sm hover:-translate-y-0.5'
                }`}
            >
              {/* Timeline node */}
              <div
                className={`absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 rounded-full border-2 z-10
                  ${
                    isSelected
                      ? 'bg-indigo-500 border-indigo-500'
                      : isLatest
                      ? 'bg-white border-indigo-400'
                      : 'bg-white border-slate-300'
                  }`}
              />

              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-sm text-slate-900">
                      v{version.version}
                    </span>
                    {isLatest && (
                      <span className="text-xs px-1.5 py-0.5 bg-indigo-50 text-indigo-600 rounded font-medium">
                        Latest
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-400">{formatDate(version.uploaded_at)}</p>
                </div>

                <div className="flex flex-col items-end gap-1.5">
                  <StatusBadge status={version.status} />
                  {diffResult && (
                    <div className="flex items-center gap-2 text-xs">
                      {breakingCount > 0 && (
                        <span className="text-red-600 font-medium">{breakingCount} breaking</span>
                      )}
                      {safeCount > 0 && (
                        <span className="text-green-600 font-medium">{safeCount} safe</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
