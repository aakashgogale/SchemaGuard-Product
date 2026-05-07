import AdminLayout from '../components/AdminLayout';

export default function AdminSettings() {
  return (
    <AdminLayout>
      <h1 className="text-2xl font-bold text-slate-900 mb-2">Settings</h1>
      <p className="text-slate-500 mb-6">Platform configuration placeholders for SMTP, AI provider, and notification policy.</p>
      <div className="card p-5 space-y-3 text-sm text-slate-600">
        <p><strong className="text-slate-900">AI Provider:</strong> Gemini</p>
        <p><strong className="text-slate-900">Notifications:</strong> Email and Slack webhooks</p>
        <p><strong className="text-slate-900">Admin policy:</strong> First registered user becomes admin automatically.</p>
      </div>
    </AdminLayout>
  );
}
