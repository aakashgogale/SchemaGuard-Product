import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  CheckCircle2,
  Code2,
  Eye,
  FileClock,
  GitBranch,
  GitCompare,
  KeyRound,
  Package,
  Plug,
  UploadCloud,
  Zap,
} from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const problems = [
  { icon: AlertTriangle, title: 'API contracts break silently', desc: 'Your consumers find out before you do. A single field rename can cascade into production outages.' },
  { icon: Eye, title: 'Code reviews miss schema changes', desc: "Diff tools don't understand API semantics. A type change looks like a one-line edit but breaks everything." },
  { icon: Package, title: 'Versioning is an afterthought', desc: 'Teams have no single source of truth for their API schemas. Versions live in Slack threads and wikis.' },
];

const steps = [
  { num: '01', title: 'Register your API', desc: 'Give your API a name and SchemaGuard creates a versioned registry for it.', icon: GitBranch },
  { num: '02', title: 'Upload a new schema version', desc: 'Paste your JSON schema or push it via the REST API from your CI pipeline.', icon: UploadCloud },
  { num: '03', title: 'Get instant breaking change analysis', desc: 'SchemaGuard compares against the previous version and tells you exactly what breaks.', icon: Zap },
];

const features = [
  { icon: AlertTriangle, title: 'Breaking change detection', desc: 'Field deletions, type changes, new required fields - caught instantly before they reach consumers.' },
  { icon: CheckCircle2, title: 'Safe change recognition', desc: 'Optional fields, description updates, loosened constraints - confirmed safe so you ship with confidence.' },
  { icon: FileClock, title: 'Version history', desc: 'Full timeline of every schema uploaded. See how your API evolved over time.' },
  { icon: GitCompare, title: 'Instant diff view', desc: 'Side-by-side JSON comparison with line-level highlights. Red for breaking, green for safe.' },
  { icon: KeyRound, title: 'JWT authentication', desc: 'Secure team access with token-based authentication. Each user owns their registries.' },
  { icon: Plug, title: 'REST API', desc: 'Integrate SchemaGuard into your CI/CD pipeline. Fail builds on breaking changes automatically.' },
];

function MiniDiff() {
  return (
    <div className="rounded-2xl border border-slate-700/70 bg-slate-800/90 shadow-2xl overflow-hidden">
      <div className="flex items-center gap-2 px-4 py-3 border-b border-slate-700/70">
        <Code2 className="w-4 h-4 text-indigo-400" />
        <span className="text-xs text-slate-400 font-mono">diff - user-api v1.2.0 to v2.0.0</span>
      </div>
      <div className="p-4 text-sm font-mono">
        <div className="flex items-center gap-2 mb-3 px-2 py-1.5 rounded bg-slate-700/40">
          <span className="text-xs font-semibold text-red-400">2 breaking</span>
          <span className="text-slate-600">/</span>
          <span className="text-xs font-semibold text-green-400">1 safe</span>
        </div>
        <div className="space-y-0.5">
          <div className="text-slate-500 px-2">{'{'}</div>
          <div className="text-slate-500 px-2">{'  "properties": {'}</div>
          <div className="text-slate-400 px-2">{'    "user_id": { "type": "string" },'}</div>
          <div className="bg-red-500/10 border-l-2 border-red-500 px-2 text-red-300">{'-   "amount": { "type": "integer" }'}</div>
          <div className="bg-red-500/10 border-l-2 border-red-500 px-2 text-red-300">{'    BREAKING: Type changed integer to number'}</div>
          <div className="bg-green-500/10 border-l-2 border-green-500 px-2 text-green-300">{'+   "currency": { "type": "string" }'}</div>
          <div className="text-slate-500 px-2">{'  }'}</div>
          <div className="text-slate-500 px-2">{'}'}</div>
        </div>
      </div>
    </div>
  );
}

export default function Landing() {
  return (
    <div className="min-h-screen">
      <Navbar />

      <section className="relative min-h-screen flex items-center bg-slate-900 overflow-hidden">
        <div className="absolute inset-0 bg-[linear-gradient(135deg,rgba(99,102,241,0.16)_0%,rgba(15,23,42,0)_42%)]" />
        <div className="relative max-w-7xl mx-auto px-6 py-32 grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          <div className="animate-fade-in">
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-indigo-500/10 border border-indigo-500/20 mb-6">
              <span className="w-2 h-2 rounded-full bg-indigo-400 animate-pulse" />
              <span className="text-xs font-medium text-indigo-400">Now in beta - free for all teams</span>
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-white leading-tight mb-6">
              Stop shipping <span className="text-gradient">breaking API changes.</span>
            </h1>
            <p className="text-lg text-slate-400 leading-relaxed mb-10 max-w-lg">
              SchemaGuard detects what breaks before your consumers do. Register your API, upload a new version, get an instant diff.
            </p>
            <div className="flex flex-wrap gap-4">
              <Link to="/signup" className="btn-primary text-base px-8 py-3.5">Start for free</Link>
              <a href="#how-it-works" className="btn-ghost text-base px-8 py-3.5">See how it works</a>
            </div>
          </div>
          <div className="animate-slide-up hidden lg:block"><MiniDiff /></div>
        </div>
      </section>

      <section className="py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">The problem with API changes</h2>
            <p className="text-slate-500 max-w-2xl mx-auto">Every team ships API changes. Most don't know which ones will break their consumers until it's too late.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {problems.map((problem) => (
              <div key={problem.title} className="card p-8 text-center group hover:-translate-y-1">
                <problem.icon className="w-9 h-9 mx-auto mb-4 text-indigo-500" />
                <h3 className="text-lg font-bold text-slate-900 mb-2">{problem.title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{problem.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="how-it-works" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">How it works</h2>
            <p className="text-slate-500">Three steps. Zero configuration. Instant results.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            <div className="hidden md:block absolute top-12 left-1/6 right-1/6 h-0.5 bg-gradient-to-r from-indigo-200 via-indigo-400 to-indigo-200" />
            {steps.map((step) => (
              <div key={step.title} className="relative text-center">
                <div className="relative z-10 w-14 h-14 rounded-2xl bg-indigo-500 text-white flex items-center justify-center mx-auto mb-6 shadow-lg shadow-indigo-500/25">
                  <step.icon className="w-7 h-7" />
                </div>
                <span className="inline-block text-xs font-bold text-indigo-500 bg-indigo-50 px-2 py-1 rounded mb-3">{step.num}</span>
                <h3 className="text-lg font-bold text-slate-900 mb-2">{step.title}</h3>
                <p className="text-sm text-slate-500">{step.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="features" className="py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-16">
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 mb-4">Everything you need</h2>
            <p className="text-slate-500">Built for teams who treat API contracts as first-class citizens.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature) => (
              <div key={feature.title} className="card p-6 group hover:-translate-y-1">
                <feature.icon className="w-8 h-8 mb-4 text-indigo-500" />
                <h3 className="text-base font-bold text-slate-900 mb-2">{feature.title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{feature.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-24 bg-slate-900">
        <div className="max-w-5xl mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">See the diff in action</h2>
            <p className="text-slate-400">Real analysis. Real results. Milliseconds, not minutes.</p>
          </div>
          <MiniDiff />
          <p className="text-center text-sm text-slate-500 mt-6">SchemaGuard runs this analysis in milliseconds.</p>
        </div>
      </section>

      <section className="py-20 bg-indigo-600">
        <div className="max-w-4xl mx-auto px-6 text-center">
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-4">Ready to protect your APIs?</h2>
          <p className="text-indigo-100 mb-10 text-lg">Start detecting breaking changes in under 2 minutes.</p>
          <div className="flex flex-wrap justify-center gap-4">
            <Link to="/signup" className="btn-primary bg-white text-indigo-600 hover:bg-slate-100 text-base px-8 py-3.5">Get started free</Link>
            <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="btn-ghost border-white/30 text-base px-8 py-3.5">View on GitHub</a>
          </div>
        </div>
      </section>

      <Footer variant="full" />
    </div>
  );
}
