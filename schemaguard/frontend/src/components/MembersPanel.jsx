import { useEffect, useMemo, useState } from 'react';
import { Check, Copy, Crown, MessageSquare, Trash2, Users } from 'lucide-react';
import { collaborationAPI } from '../api/client';

function errorMessage(error, fallback) {
  return error.response?.data?.message || error.response?.data?.detail?.[0]?.message || fallback;
}

function StatusDot({ status }) {
  const color = status === 'online' ? 'bg-green-500' : status === 'away' ? 'bg-amber-500' : 'bg-slate-400';
  return <span className={`absolute -right-0.5 -bottom-0.5 h-3 w-3 rounded-full border-2 border-white ${color}`} />;
}

function relativeTime(value) {
  if (!value) return 'never';
  const diff = Math.max(0, Date.now() - new Date(value).getTime());
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes} min ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hours ago`;
  return `${Math.floor(hours / 24)} days ago`;
}

export default function MembersPanel({ registryId, publicToken }) {
  const [activeTab, setActiveTab] = useState('members');
  const [members, setMembers] = useState([]);
  const [teamRows, setTeamRows] = useState([]);
  const [activity, setActivity] = useState([]);
  const [subscribers, setSubscribers] = useState([]);
  const [messages, setMessages] = useState([]);
  const [memberEmail, setMemberEmail] = useState('');
  const [subscriberEmail, setSubscriberEmail] = useState('');
  const [teamName, setTeamName] = useState('');
  const [webhookUrl, setWebhookUrl] = useState('');
  const [notifyBreakingOnly, setNotifyBreakingOnly] = useState(true);
  const [messageText, setMessageText] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  const publicDiffUrl = useMemo(() => `${window.location.origin}/public/diff/${publicToken}`, [publicToken]);
  const publicConversationUrl = useMemo(() => `${window.location.origin}/public/conversation/${publicToken}`, [publicToken]);
  const lead = subscribers.find((item) => item.is_lead);

  const load = async () => {
    setLoading(true);
    setError('');
    try {
      const [memberData, subscriberData, teamData, messageData] = await Promise.all([
        collaborationAPI.listMembers(registryId),
        collaborationAPI.listSubscribers(registryId),
        collaborationAPI.teamActivity(registryId),
        collaborationAPI.listMessages(registryId).catch(() => ({ messages: [] })),
      ]);
      setMembers(memberData.members || []);
      setSubscribers(subscriberData.subscribers || []);
      setTeamRows(teamData.members || []);
      setActivity(teamData.activity || []);
      setMessages(messageData.messages || []);
    } catch (err) {
      setError(errorMessage(err, 'Could not load team settings.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [registryId]);

  const copyLink = async (url) => {
    await navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  const addMember = async (event) => {
    event.preventDefault();
    try {
      await collaborationAPI.addMember(registryId, { email: memberEmail.trim() });
      setMemberEmail('');
      load();
    } catch (err) {
      setError(errorMessage(err, 'Could not add member.'));
    }
  };

  const addSubscriber = async (event) => {
    event.preventDefault();
    try {
      await collaborationAPI.addSubscriber(registryId, {
        email: subscriberEmail.trim(),
        team_name: teamName.trim() || null,
        webhook_url: webhookUrl.trim() || null,
        notify_breaking_only: notifyBreakingOnly,
      });
      setSubscriberEmail('');
      setTeamName('');
      setWebhookUrl('');
      setNotifyBreakingOnly(true);
      load();
    } catch (err) {
      setError(errorMessage(err, 'Could not add subscriber.'));
    }
  };

  const sendMessage = async (event) => {
    event.preventDefault();
    if (!messageText.trim()) return;
    await collaborationAPI.sendMessage(registryId, { content: messageText.trim() });
    setMessageText('');
    load();
  };

  return (
    <div className="space-y-6">
      <div className="card p-5">
        <div className="flex items-center gap-2 mb-3">
          <Users className="w-5 h-5 text-indigo-500" />
          <h3 className="font-semibold text-slate-900">Public Diff Link</h3>
        </div>
        <p className="text-sm text-slate-500 mb-3">Share this link with Team B - they can see diffs without a SchemaGuard account.</p>
        <div className="flex flex-col sm:flex-row gap-3">
          <input readOnly value={publicDiffUrl} className="input-field font-mono text-xs" />
          <button type="button" onClick={() => copyLink(publicDiffUrl)} className="btn-secondary whitespace-nowrap">
            {copied ? <Check className="w-4 h-4 mr-2" /> : <Copy className="w-4 h-4 mr-2" />}
            {copied ? 'Copied!' : 'Copy Link'}
          </button>
        </div>
      </div>

      <div className="card overflow-hidden">
        <div className="border-b border-slate-200 flex">
          <button onClick={() => setActiveTab('members')} className={`px-5 py-3 text-sm font-semibold ${activeTab === 'members' ? 'text-indigo-600 border-b-2 border-indigo-500' : 'text-slate-500'}`}>Team Members</button>
          <button onClick={() => setActiveTab('subscribers')} className={`px-5 py-3 text-sm font-semibold ${activeTab === 'subscribers' ? 'text-indigo-600 border-b-2 border-indigo-500' : 'text-slate-500'}`}>Subscribers</button>
        </div>

        {error && <div className="mx-5 mt-5 rounded-lg bg-red-50 border border-red-200 p-3 text-sm text-red-600">{error}</div>}
        {loading ? (
          <div className="p-5 text-slate-500">Loading team settings...</div>
        ) : activeTab === 'members' ? (
          <div className="p-5 space-y-6">
            <form onSubmit={addMember} className="flex flex-col sm:flex-row gap-3">
              <input type="email" className="input-field" placeholder="teammate@company.com" value={memberEmail} onChange={(e) => setMemberEmail(e.target.value)} required />
              <button className="btn-primary whitespace-nowrap">Add Member</button>
            </form>
            <div className="divide-y divide-slate-100">
              {teamRows.map((row) => {
                const member = members.find((item) => item.email === row.email);
                return (
                  <div key={row.email} className="py-4 flex flex-col lg:flex-row lg:items-center justify-between gap-3">
                    <div className="flex items-center gap-3">
                      <div className="relative h-10 w-10 rounded-full bg-indigo-50 text-indigo-600 flex items-center justify-center font-bold">
                        {row.role === 'OWNER' ? <Crown className="w-5 h-5 text-amber-500" /> : row.email.charAt(0).toUpperCase()}
                        <StatusDot status={row.activity_status} />
                      </div>
                      <div>
                        <p className="font-semibold text-slate-800">{row.email}</p>
                        <p className="text-xs text-slate-400">{relativeTime(row.last_active_at)} · {row.total_uploads_for_this_registry} uploads</p>
                      </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`rounded-full px-2 py-1 text-xs font-semibold ${row.role === 'OWNER' ? 'bg-amber-50 text-amber-700' : row.role === 'CO_LEAD' ? 'bg-purple-50 text-purple-700' : 'bg-slate-100 text-slate-600'}`}>{row.role === 'CO_LEAD' ? 'Co-Lead' : row.role}</span>
                      {member && (
                        <select value={member.role} onChange={(event) => collaborationAPI.updateMemberRole(registryId, member.id, { role: event.target.value }).then(load)} className="input-field py-2 text-sm max-w-36">
                          <option value="CO_LEAD">Co-Lead</option>
                          <option value="MEMBER">Member</option>
                        </select>
                      )}
                      {member && <button onClick={() => collaborationAPI.removeMember(registryId, member.id).then(load)} className="btn-danger"><Trash2 className="w-4 h-4" /></button>}
                    </div>
                  </div>
                );
              })}
            </div>
            <div>
              <h4 className="font-bold text-slate-900 mb-3">Team Activity</h4>
              <div className="space-y-3">
                {activity.length === 0 ? <p className="text-sm text-slate-400">No activity yet.</p> : activity.map((item) => (
                  <div key={item.id} className="flex items-start gap-3 rounded-lg bg-slate-50 p-3 text-sm">
                    <MessageSquare className="w-4 h-4 text-indigo-500 mt-0.5" />
                    <div>
                      <p className="text-slate-700">{item.human_readable_description}</p>
                      <p className="text-xs text-slate-400">{item.relative_time}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="p-5 space-y-6">
            <form onSubmit={addSubscriber} className="grid grid-cols-1 lg:grid-cols-2 gap-3">
              <input type="email" className="input-field" placeholder="consumer@company.com" value={subscriberEmail} onChange={(e) => setSubscriberEmail(e.target.value)} required />
              <input className="input-field" placeholder="Team name (optional)" value={teamName} onChange={(e) => setTeamName(e.target.value)} />
              <input type="url" className="input-field" placeholder="Slack webhook URL (optional)" value={webhookUrl} onChange={(e) => setWebhookUrl(e.target.value)} />
              <label className="flex items-center gap-2 text-sm text-slate-600">
                <input type="checkbox" checked={notifyBreakingOnly} onChange={(e) => setNotifyBreakingOnly(e.target.checked)} />
                Notify on breaking changes only
              </label>
              <button className="btn-primary lg:col-span-2">Add Subscriber</button>
            </form>
            {subscribers.length === 0 ? (
              <p className="text-sm text-slate-400">No subscribers yet. Add Team B emails to notify them when your API breaks.</p>
            ) : (
              <div className="divide-y divide-slate-100">
                {subscribers.map((subscriber) => (
                  <div key={subscriber.id} className="py-4 flex flex-col lg:flex-row lg:items-center justify-between gap-3">
                    <div>
                      <p className="font-semibold text-slate-800">{subscriber.email}</p>
                      {subscriber.team_name && <p className="text-xs text-slate-400">{subscriber.team_name}</p>}
                      <div className="mt-1 flex flex-wrap gap-2">
                        {subscriber.is_lead && <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs font-semibold text-amber-700">Team Lead</span>}
                        <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">{subscriber.notify_breaking_only ? 'Breaking only' : 'All changes'}</span>
                        {subscriber.webhook_url && <span className="rounded-full bg-green-50 px-2 py-0.5 text-xs text-green-700">Slack ✓</span>}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      {!subscriber.is_lead && <button onClick={() => collaborationAPI.makeSubscriberLead(registryId, subscriber.id).then(load)} className="btn-secondary">Make Lead</button>}
                      <button onClick={() => collaborationAPI.removeSubscriber(registryId, subscriber.id).then(load)} className="btn-danger"><Trash2 className="w-4 h-4" /></button>
                    </div>
                  </div>
                ))}
              </div>
            )}
            <div className="rounded-xl border border-slate-200 p-4">
              {lead ? (
                <>
                  <div className="mb-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                    <h4 className="font-bold text-slate-900">Conversation with {lead.email}</h4>
                    <button onClick={() => copyLink(publicConversationUrl)} className="btn-secondary text-sm">Copy public reply link</button>
                  </div>
                  <div className="max-h-80 overflow-y-auto space-y-3 mb-4">
                    {messages.map((message) => (
                      <div key={message.id} className={`flex ${message.sender_type === 'TEAM_A' ? 'justify-end' : 'justify-start'}`}>
                        <div className={`max-w-[82%] rounded-2xl px-4 py-3 text-sm ${message.sender_type === 'TEAM_A' ? 'bg-indigo-500 text-white' : 'bg-white border border-slate-200 text-slate-800'}`}>
                          <p className="text-xs opacity-80">{message.sender_email}</p>
                          <p className="whitespace-pre-wrap">{message.content}</p>
                          {!message.is_read && message.sender_type === 'TEAM_B' && <span className="inline-block h-2 w-2 rounded-full bg-blue-500" />}
                        </div>
                      </div>
                    ))}
                  </div>
                  <form onSubmit={sendMessage} className="space-y-3">
                    <textarea className="input-field min-h-24" value={messageText} onChange={(e) => setMessageText(e.target.value)} placeholder="Write a message to Team B Lead..." maxLength={2000} />
                    <button className="btn-primary">Send Message</button>
                  </form>
                </>
              ) : (
                <p className="text-sm text-slate-500">Set a subscriber as Team Lead to enable messaging.</p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
