import { useState } from 'react';
import { Loader2 } from 'lucide-react';
import { versionsAPI } from '../api/client';

export default function SchemaUploader({ registryId, onSuccess }) {
  const [version, setVersion] = useState('');
  const [schemaText, setSchemaText] = useState('');
  const [changeReason, setChangeReason] = useState('');
  const [error, setError] = useState('');
  const [parseError, setParseError] = useState('');
  const [loading, setLoading] = useState(false);

  const semverRegex = /^\d+\.\d+\.\d+$/;

  const validateJson = () => {
    setParseError('');
    try {
      const parsed = JSON.parse(schemaText);
      if (typeof parsed !== 'object' || Array.isArray(parsed)) {
        setParseError('Schema must be a JSON object');
        return null;
      }
      if (!parsed.properties && !parsed.paths) {
        setParseError('Schema must have "properties" or "paths" key');
        return null;
      }
      return parsed;
    } catch (e) {
      setParseError(`Invalid JSON: ${e.message}`);
      return null;
    }
  };

  const handleValidate = () => {
    const parsed = validateJson();
    if (parsed) {
      setParseError('');
      setError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setParseError('');

    if (!semverRegex.test(version)) {
      setError('Version must be in semver format (e.g., 1.0.0)');
      return;
    }

    const parsed = validateJson();
    if (!parsed) return;

    setLoading(true);
    try {
      await versionsAPI.upload(registryId, {
        version,
        schema_json: parsed,
        change_reason: changeReason.trim() || null,
      });
      setVersion('');
      setSchemaText('');
      setChangeReason('');
      if (onSuccess) onSuccess();
    } catch (err) {
      const message = err.response?.data?.message || err.response?.data?.error || 'Upload failed';
      setError(typeof message === 'string' ? message : 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label htmlFor="upload-version" className="label">Version</label>
        <input
          id="upload-version"
          type="text"
          value={version}
          onChange={(e) => setVersion(e.target.value)}
          placeholder="1.0.0"
          className={`input-field font-mono ${error && !semverRegex.test(version) ? 'border-red-400 focus:ring-red-500' : ''}`}
        />
        <p className="text-xs text-slate-400 mt-1">Semantic versioning: major.minor.patch</p>
      </div>

      <div>
        <label htmlFor="upload-schema" className="label">Schema JSON</label>
        <textarea
          id="upload-schema"
          value={schemaText}
          onChange={(e) => setSchemaText(e.target.value)}
          placeholder={`{
  "properties": {
    "user_id": { "type": "string" },
    "amount": { "type": "integer" }
  },
  "required": ["user_id"]
}`}
          rows={10}
          className={`input-field font-mono text-sm resize-y ${parseError ? 'border-red-400 focus:ring-red-500' : ''}`}
        />
        {parseError && <p className="error-text">{parseError}</p>}
      </div>

      <div>
        <label htmlFor="change-reason" className="label">Change reason (optional)</label>
        <input
          id="change-reason"
          type="text"
          value={changeReason}
          onChange={(e) => setChangeReason(e.target.value)}
          placeholder="e.g. Removed user_id - now using Bearer token for auth"
          className="input-field"
          maxLength={500}
        />
        <p className="text-xs text-slate-400 mt-1">This message will be included in all notification emails.</p>
      </div>

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={handleValidate}
          className="btn-secondary text-sm px-4 py-2"
          disabled={!schemaText.trim()}
        >
          Validate JSON
        </button>
        <button
          type="submit"
          className="btn-primary text-sm px-4 py-2"
          disabled={loading || !version.trim() || !schemaText.trim()}
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <Loader2 className="animate-spin w-4 h-4" />
              Running diff engine...
            </span>
          ) : (
            'Upload & analyze'
          )}
        </button>
      </div>

      {error && <p className="error-text">{error}</p>}
    </form>
  );
}
