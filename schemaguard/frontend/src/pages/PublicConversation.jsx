import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { ShieldCheck } from 'lucide-react';
import { publicAPI } from '../api/client';

export default function PublicConversation() {
  const { token } = useParams();
  const [data, setData] = useState(null);
  const [email, setEmail] = useState('');
  const [content, setContent] = useState('');
  const [status, setStatus] = useState('');
  const [error, setError] = useState('');
  const load = () => publicAPI.getConversation(token).then(setData).catch(() => setError('This conversation link is invalid.'));
  useEffect(() => { load(); }, [token]);
  const submit = async (event) => {
    event.preventDefault();
    setError('');
    setStatus('');
    try {
      await publicAPI.sendConversationMessage(token, { email, content });
      setContent('');
      setStatus('Reply sent. Team A will be notified.');
      load();
    } catch {
      setError('Your email does not match the Team Lead on file.');
    }
  };
  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200 px-5 py-4 flex items-center gap-2">
        <ShieldCheck className="w-5 h-5 text-indigo-500" />
        <span className="font-bold text-slate-900">SchemaGuard</span>
      </header>
      <main className="max-w-4xl mx-auto p-5">
        <h1 className="text-2xl font-bold text-slate-900 mb-4">Conversation — {data?.registry_name || 'Loading'}</h1>
        <div className="card p-5 min-h-[420px] space-y-4">
          {(data?.messages || []).map((message) => (
            <div key={message.id} className={`flex ${message.sender_type === 'TEAM_A' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[82%] rounded-2xl px-4 py-3 text-sm ${message.sender_type === 'TEAM_A' ? 'bg-indigo-500 text-white' : 'bg-white border border-slate-200 text-slate-800'}`}>
                <p className="font-semibold text-xs opacity-80">{message.sender_email}</p>
                <p className="mt-1 whitespace-pre-wrap">{message.content}</p>
                <p className="mt-1 text-xs opacity-70">{new Date(message.sent_at).toLocaleString()}</p>
              </div>
            </div>
          ))}
        </div>
        <form onSubmit={submit} className="card p-5 mt-4 space-y-3">
          <input className="input-field" type="email" placeholder="Your email (must match your subscription email)" value={email} onChange={(event) => setEmail(event.target.value)} required />
          <textarea className="input-field min-h-28" placeholder="Type your reply..." value={content} onChange={(event) => setContent(event.target.value)} required maxLength={2000} />
          {status && <p className="text-sm text-green-600">{status}</p>}
          {error && <p className="text-sm text-red-600">{error}</p>}
          <button className="btn-primary">Send Reply</button>
        </form>
      </main>
    </div>
  );
}
