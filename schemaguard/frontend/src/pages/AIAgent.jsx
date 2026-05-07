import { useEffect, useRef, useState } from 'react';
import { ArrowUp, Bot, RotateCcw, ShieldCheck, Sparkles } from 'lucide-react';
import AppLayout from '../components/AppLayout';
import { agentAPI } from '../api/client';

const suggestions = [
  'Is it safe to deploy my latest version?',
  'What breaking changes happened recently?',
  'Which of my APIs has the most risk?',
  'How do I communicate this change to my team?',
];

function timeLabel(date) {
  return new Intl.DateTimeFormat('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

function TypingBubble() {
  return (
    <div className="flex items-start gap-3">
      <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center flex-shrink-0">
        <ShieldCheck className="w-4 h-4" />
      </div>
      <div className="rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm">
        <div className="flex gap-1">
          <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" />
          <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce [animation-delay:120ms]" />
          <span className="w-2 h-2 rounded-full bg-slate-400 animate-bounce [animation-delay:240ms]" />
        </div>
      </div>
    </div>
  );
}

export default function AIAgent() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [lastMessage, setLastMessage] = useState('');
  const [stats, setStats] = useState(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    agentAPI.stats().then(setStats).catch(() => setStats(null));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading, error]);

  useEffect(() => {
    if (error.includes('GEMINI_API_KEY')) {
      setError('');
    }
  }, [error]);

  const sendMessage = async (content) => {
    const trimmed = content.trim();
    if (!trimmed || loading) return;

    const history = messages
      .filter((message) => message.role === 'user' || message.role === 'assistant')
      .slice(-20)
      .map(({ role, content: text }) => ({ role, content: text }));
    const userMessage = { role: 'user', content: trimmed, createdAt: new Date() };
    setMessages((current) => [...current, userMessage]);
    setInput('');
    setError('');
    setLastMessage(trimmed);
    setLoading(true);

    try {
      const response = await agentAPI.chat({
        message: trimmed,
        conversation_history: history,
      });
      setMessages((current) => [
        ...current,
        { role: 'assistant', content: response.reply, createdAt: new Date() },
      ]);
    } catch (err) {
      const message = err.response?.data?.message || 'AI service temporarily unavailable.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    sendMessage(input);
  };

  const onKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage(input);
    }
  };

  const remaining = 1000 - input.length;

  return (
    <AppLayout>
      <div className="flex h-[calc(100vh-8rem)] gap-6">
        <section className="flex min-w-0 flex-1 flex-col">
          <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">SchemaGuard AI Agent</h1>
              <p className="text-sm text-slate-500 mt-1">Ask anything about your APIs, schema changes, and release safety</p>
            </div>
            <a
              href="https://gemini.google.com"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 rounded-full border border-indigo-100 bg-indigo-50 px-3 py-1.5 text-sm font-medium text-indigo-700"
            >
              <Sparkles className="w-4 h-4" />
              Powered by Gemini
            </a>
          </div>

          <div className="card flex min-h-0 flex-1 flex-col overflow-hidden">
            <div className="flex-1 overflow-y-auto p-5 space-y-5">
              {messages.length === 0 && !loading && (
                <div className="h-full flex flex-col items-center justify-center text-center">
                  <Bot className="w-10 h-10 text-indigo-500 mb-4" />
                  <h2 className="font-bold text-slate-900 mb-2">What do you want to know?</h2>
                  <p className="text-sm text-slate-500 mb-5">The agent reads your real registries, versions, and diff results before answering.</p>
                  <div className="flex flex-wrap justify-center gap-2 max-w-2xl">
                    {suggestions.map((suggestion) => (
                      <button
                        key={suggestion}
                        onClick={() => sendMessage(suggestion)}
                        className="rounded-full border border-slate-200 bg-white px-4 py-2 text-sm text-slate-700 hover:border-indigo-300 hover:text-indigo-600 transition-all"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((message, index) => (
                <div key={`${message.role}-${index}`} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                  {message.role === 'assistant' && (
                    <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center flex-shrink-0 mr-3">
                      <ShieldCheck className="w-4 h-4" />
                    </div>
                  )}
                  <div className={`max-w-[82%] rounded-2xl px-4 py-3 text-sm leading-6 whitespace-pre-wrap select-text ${
                    message.role === 'user'
                      ? 'bg-indigo-500 text-white'
                      : 'bg-white text-slate-800 border border-slate-200 shadow-sm'
                  }`}>
                    {message.content}
                    <div className={`mt-1 text-[11px] ${message.role === 'user' ? 'text-indigo-100' : 'text-slate-400'}`}>
                      {timeLabel(message.createdAt)}
                    </div>
                  </div>
                </div>
              ))}

              {loading && <TypingBubble />}
              {error && (
                <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
                  <p>{error}</p>
                  {lastMessage && (
                    <button onClick={() => sendMessage(lastMessage)} className="mt-3 inline-flex items-center gap-2 font-semibold text-red-700 hover:text-red-800">
                      <RotateCcw className="w-4 h-4" /> Try again
                    </button>
                  )}
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            <form onSubmit={handleSubmit} className="border-t border-slate-200 bg-white p-4">
              <div className="flex items-end gap-3">
                <textarea
                  value={input}
                  onChange={(event) => setInput(event.target.value.slice(0, 1000))}
                  onKeyDown={onKeyDown}
                  disabled={loading}
                  placeholder="Ask about your APIs..."
                  rows={1}
                  className="input-field max-h-32 resize-none"
                />
                <button className="btn-primary h-12 w-12 px-0" disabled={loading || !input.trim()}>
                  <ArrowUp className="w-5 h-5" />
                </button>
              </div>
              <div className={`mt-2 text-right text-xs ${remaining < 100 ? 'text-amber-600' : 'text-slate-400'}`}>
                {remaining} characters remaining
              </div>
            </form>
          </div>
        </section>

        <aside className="hidden xl:block w-64 flex-shrink-0">
          <div className="card p-5 sticky top-8">
            <h2 className="font-bold text-slate-900 mb-4">Your Context</h2>
            <div className="space-y-4 text-sm">
              <div><p className="text-slate-500">Total APIs</p><p className="text-2xl font-bold text-slate-900">{stats?.total_apis ?? '-'}</p></div>
              <div><p className="text-slate-500">Breaking changes this week</p><p className="text-2xl font-bold text-red-600">{stats?.breaking_changes_this_week ?? '-'}</p></div>
              <div><p className="text-slate-500">Last upload time</p><p className="font-medium text-slate-800">{stats?.last_upload_time ? new Date(stats.last_upload_time).toLocaleString() : 'No uploads yet'}</p></div>
            </div>
            <p className="mt-5 rounded-lg bg-slate-50 p-3 text-xs text-slate-500">The AI Agent reads this data to answer your questions.</p>
          </div>
        </aside>
      </div>
    </AppLayout>
  );
}
