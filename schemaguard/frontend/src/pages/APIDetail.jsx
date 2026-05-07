import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ChevronRight, FileText, UploadCloud } from 'lucide-react';
import { registryAPI } from '../api/client';
import Sidebar from '../components/Sidebar';
import Footer from '../components/Footer';
import VersionTimeline from '../components/VersionTimeline';
import DiffPanel from '../components/DiffPanel';
import SchemaUploader from '../components/SchemaUploader';
import MembersPanel from '../components/MembersPanel';

const tabs = ['Versions', 'Team & Notifications', 'Settings'];

export default function APIDetail() {
  const { id } = useParams();
  const [registry, setRegistry] = useState(null);
  const [versions, setVersions] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [activeTab, setActiveTab] = useState('Versions');
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);

  const fetchData = async () => {
    try {
      const data = await registryAPI.get(id);
      setRegistry(data);
      setVersions(data.versions || []);
      if (data.versions?.length > 0 && !selectedId) {
        setSelectedId(data.versions[0].id);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [id]);

  const selectedVersion = versions.find((version) => version.id === selectedId);
  const selectedIdx = versions.findIndex((version) => version.id === selectedId);
  const prevVersion = selectedIdx < versions.length - 1 ? versions[selectedIdx + 1] : null;

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar />
      <div className="flex-1 flex flex-col min-h-screen">
        <main className="flex-1 p-6 lg:p-10 pt-20 lg:pt-10">
          {loading ? (
            <div className="animate-pulse space-y-4">
              <div className="skeleton h-6 w-48" />
              <div className="skeleton h-4 w-72" />
              <div className="skeleton h-64 w-full rounded-xl mt-8" />
            </div>
          ) : registry ? (
            <>
              <div className="flex items-center gap-2 text-sm text-slate-400 mb-6">
                <Link to="/apis" className="hover:text-indigo-500 transition-colors">APIs</Link>
                <ChevronRight className="w-4 h-4" />
                <span className="text-slate-700 font-medium">{registry.name}</span>
              </div>

              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 mb-6">
                <div>
                  <h1 className="text-2xl font-bold text-slate-900">{registry.name}</h1>
                  {registry.description && <p className="text-sm text-slate-500 mt-1">{registry.description}</p>}
                  <p className="text-xs text-slate-400 mt-2">Created {new Date(registry.created_at).toLocaleDateString()}</p>
                </div>
                <button onClick={() => setShowUpload(true)} className="btn-primary text-sm">
                  <UploadCloud className="w-4 h-4 mr-2" />
                  Upload new version
                </button>
              </div>

              <div className="mb-6 border-b border-slate-200 flex gap-1">
                {tabs.map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`px-4 py-3 text-sm font-semibold border-b-2 transition-colors ${
                      activeTab === tab ? 'border-indigo-500 text-indigo-600' : 'border-transparent text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              {activeTab === 'Versions' && (
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="lg:col-span-1">
                    <div className="card p-4">
                      <h3 className="text-sm font-semibold text-slate-700 mb-4">Version Timeline</h3>
                      <VersionTimeline versions={versions} selectedId={selectedId} onSelect={setSelectedId} />
                    </div>
                  </div>
                  <div className="lg:col-span-2">
                    {selectedVersion ? (
                      selectedVersion.diff_result ? (
                        <DiffPanel
                          changes={selectedVersion.diff_result.changes || []}
                          v1Schema={prevVersion?.schema_json || {}}
                          v2Schema={selectedVersion.schema_json || {}}
                        />
                      ) : (
                        <div className="card p-8 text-center">
                          <FileText className="w-10 h-10 mx-auto mb-3 text-slate-300" />
                          <p className="text-slate-600 font-medium">First version - v{selectedVersion.version}</p>
                          <p className="text-sm text-slate-400 mt-1">No previous version to compare against.</p>
                        </div>
                      )
                    ) : (
                      <div className="card p-8 text-center text-slate-400">
                        <p>Select a version from the timeline to view its diff</p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {activeTab === 'Team & Notifications' && (
                <MembersPanel registryId={registry.id} publicToken={registry.public_token} />
              )}

              {activeTab === 'Settings' && (
                <div className="card p-6">
                  <h2 className="font-bold text-slate-900 mb-2">Registry settings</h2>
                  <p className="text-sm text-slate-500">Delete and rename controls can be added here later. Team notification controls live in the Team & Notifications tab.</p>
                </div>
              )}
            </>
          ) : (
            <div className="text-center py-20">
              <p className="text-slate-500">Registry not found</p>
              <Link to="/apis" className="text-indigo-500 text-sm font-medium mt-2 inline-block">Back to APIs</Link>
            </div>
          )}
        </main>
        <Footer variant="minimal" />
      </div>

      {showUpload && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setShowUpload(false)} />
          <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-lg p-6 animate-fade-in max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-bold text-slate-900 mb-1">Upload new version</h2>
            <p className="text-sm text-slate-500 mb-6">Upload a JSON schema to analyze for breaking changes.</p>
            <SchemaUploader registryId={id} onSuccess={() => { setShowUpload(false); fetchData(); }} />
            <button onClick={() => setShowUpload(false)} className="mt-4 text-sm text-slate-400 hover:text-slate-600 transition-colors">Cancel</button>
          </div>
        </div>
      )}
    </div>
  );
}
