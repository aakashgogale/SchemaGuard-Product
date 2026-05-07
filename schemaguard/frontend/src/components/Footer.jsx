import { Github, Linkedin, ShieldCheck, Twitter } from 'lucide-react';

export default function Footer({ variant = 'full' }) {
  if (variant === 'minimal') {
    return (
      <footer className="py-6 px-6 text-center border-t border-slate-200 bg-white">
        <p className="text-sm text-slate-400">
          © {new Date().getFullYear()} SchemaGuard. Built for engineers who care about contracts.
        </p>
      </footer>
    );
  }

  return (
    <footer className="bg-slate-900 text-slate-400">
      <div className="max-w-7xl mx-auto px-6 py-16">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-12">
          <div className="md:col-span-1">
            <div className="flex items-center gap-2 text-white font-bold text-lg mb-4">
              <ShieldCheck className="w-5 h-5 text-indigo-400" />
              <span>SchemaGuard</span>
            </div>
            <p className="text-sm text-slate-500 leading-relaxed">
              Know before you ship. Detect breaking API changes instantly.
            </p>
            <div className="flex gap-4 mt-6">
              <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="text-slate-500 hover:text-white transition-colors duration-200" aria-label="GitHub">
                <Github className="w-5 h-5" />
              </a>
              <a href="https://twitter.com" target="_blank" rel="noopener noreferrer" className="text-slate-500 hover:text-white transition-colors duration-200" aria-label="Twitter">
                <Twitter className="w-5 h-5" />
              </a>
              <a href="https://linkedin.com" target="_blank" rel="noopener noreferrer" className="text-slate-500 hover:text-white transition-colors duration-200" aria-label="LinkedIn">
                <Linkedin className="w-5 h-5" />
              </a>
            </div>
          </div>

          <div>
            <h4 className="text-white text-sm font-semibold mb-4 uppercase tracking-wider">Product</h4>
            <ul className="space-y-3">
              <li><a href="#features" className="text-sm hover:text-white transition-colors duration-200">Features</a></li>
              <li><a href="#" className="text-sm hover:text-white transition-colors duration-200">Docs</a></li>
              <li><a href="#" className="text-sm hover:text-white transition-colors duration-200">Changelog</a></li>
            </ul>
          </div>

          <div>
            <h4 className="text-white text-sm font-semibold mb-4 uppercase tracking-wider">Company</h4>
            <ul className="space-y-3">
              <li><a href="#" className="text-sm hover:text-white transition-colors duration-200">About</a></li>
              <li><a href="#" className="text-sm hover:text-white transition-colors duration-200">Blog</a></li>
              <li><a href="#" className="text-sm hover:text-white transition-colors duration-200">Careers</a></li>
            </ul>
          </div>

          <div>
            <h4 className="text-white text-sm font-semibold mb-4 uppercase tracking-wider">Legal</h4>
            <ul className="space-y-3">
              <li><a href="#" className="text-sm hover:text-white transition-colors duration-200">Privacy</a></li>
              <li><a href="#" className="text-sm hover:text-white transition-colors duration-200">Terms</a></li>
            </ul>
          </div>
        </div>

        <div className="mt-16 pt-8 border-t border-slate-800">
          <p className="text-sm text-slate-500 text-center">
            © {new Date().getFullYear()} SchemaGuard. Built for engineers who care about contracts.
          </p>
        </div>
      </div>
    </footer>
  );
}
