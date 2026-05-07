import StatusBadge from './StatusBadge';

function syntaxHighlight(json) {
  if (typeof json !== 'string') {
    json = JSON.stringify(json, null, 2);
  }
  return json.replace(
    /("(\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+-]?\d+)?)/g,
    (match) => {
      let cls = 'json-number';
      if (/^"/.test(match)) {
        if (/:$/.test(match)) {
          cls = 'json-key';
        } else {
          cls = 'json-string';
        }
      } else if (/true|false/.test(match)) {
        cls = 'json-boolean';
      } else if (/null/.test(match)) {
        cls = 'json-null';
      }
      return `<span class="${cls}">${match}</span>`;
    }
  );
}

function getChangedPaths(changes, changeType) {
  return changes
    .filter((c) => !changeType || c.change_type === changeType)
    .map((c) => c.path);
}

function renderJsonWithHighlights(schema, changes, side) {
  const jsonStr = JSON.stringify(schema, null, 2);
  const lines = jsonStr.split('\n');

  return lines.map((line, idx) => {
    let bgClass = '';
    let prefix = ' ';

    const breakingPaths = getChangedPaths(changes, 'BREAKING');
    const safePaths = getChangedPaths(changes, 'SAFE');

    for (const path of breakingPaths) {
      const fieldName = path.split('.').pop();
      if (fieldName && line.includes(`"${fieldName}"`)) {
        bgClass = side === 'old' ? 'bg-red-50 border-l-2 border-red-500' : 'bg-red-50 border-l-2 border-red-500';
        prefix = side === 'old' ? '-' : '+';
        break;
      }
    }

    if (!bgClass) {
      for (const path of safePaths) {
        const fieldName = path.split('.').pop();
        if (fieldName && line.includes(`"${fieldName}"`)) {
          bgClass = 'bg-green-50 border-l-2 border-green-500';
          prefix = '+';
          break;
        }
      }
    }

    return (
      <div key={idx} className={`flex ${bgClass}`}>
        <span className="w-10 flex-shrink-0 text-right pr-3 text-slate-400 text-xs leading-6 select-none">
          {idx + 1}
        </span>
        <span className="w-4 flex-shrink-0 text-center text-xs leading-6 select-none text-slate-400">
          {prefix !== ' ' ? prefix : ''}
        </span>
        <code
          className="flex-1 text-sm leading-6 font-mono px-2"
          dangerouslySetInnerHTML={{ __html: syntaxHighlight(line) }}
        />
      </div>
    );
  });
}

export default function DiffPanel({ changes = [], v1Schema = {}, v2Schema = {} }) {
  const breakingChanges = changes.filter((c) => c.change_type === 'BREAKING');
  const safeChanges = changes.filter((c) => c.change_type === 'SAFE');

  return (
    <div className="space-y-4">
      {/* Summary bar */}
      <div className="flex flex-wrap items-center gap-3 p-4 bg-slate-50 rounded-xl border border-slate-200">
        <StatusBadge status="BREAKING" />
        <span className="text-sm font-medium text-slate-700">
          {breakingChanges.length} breaking {breakingChanges.length === 1 ? 'change' : 'changes'}
        </span>
        <span className="text-slate-300">·</span>
        <StatusBadge status="SAFE" />
        <span className="text-sm font-medium text-slate-700">
          {safeChanges.length} safe {safeChanges.length === 1 ? 'change' : 'changes'}
        </span>
      </div>

      {/* Change details */}
      {changes.length > 0 && (
        <div className="space-y-2">
          {changes.map((change, idx) => (
            <div
              key={idx}
              className={`p-3 rounded-lg border text-sm ${
                change.change_type === 'BREAKING'
                  ? 'bg-red-50 border-red-200'
                  : 'bg-green-50 border-green-200'
              }`}
            >
              <div className="flex items-center gap-2 mb-1">
                <StatusBadge status={change.change_type} />
                <code className="text-xs font-mono text-slate-600">{change.path}</code>
              </div>
              <p className="text-slate-700">{change.reason}</p>
            </div>
          ))}
        </div>
      )}

      {/* Side-by-side panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="card overflow-hidden">
          <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-200">
            <span className="text-sm font-semibold text-slate-700">Previous Version</span>
          </div>
          <div className="overflow-x-auto max-h-96 overflow-y-auto bg-white">
            {renderJsonWithHighlights(v1Schema, changes, 'old')}
          </div>
        </div>

        <div className="card overflow-hidden">
          <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-200">
            <span className="text-sm font-semibold text-slate-700">New Version</span>
          </div>
          <div className="overflow-x-auto max-h-96 overflow-y-auto bg-white">
            {renderJsonWithHighlights(v2Schema, changes, 'new')}
          </div>
        </div>
      </div>
    </div>
  );
}
