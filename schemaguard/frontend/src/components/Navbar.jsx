import { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, ShieldCheck, X } from 'lucide-react';

export default function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const location = useLocation();
  const isLanding = location.pathname === '/';

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navBg = scrolled || !isLanding
    ? 'bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-sm'
    : 'bg-transparent';

  const textColor = scrolled || !isLanding ? 'text-slate-700' : 'text-slate-300';
  const logoColor = scrolled || !isLanding ? 'text-slate-900' : 'text-white';

  const scrollToSection = (id) => {
    const el = document.getElementById(id);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
      setMobileOpen(false);
    }
  };

  return (
    <>
      <nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${navBg}`}
      >
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className={`flex items-center gap-2 font-bold text-lg ${logoColor} transition-colors duration-200`}>
            <ShieldCheck className="w-5 h-5 text-indigo-500" />
            <span>SchemaGuard</span>
          </Link>

          {/* Desktop nav */}
          <div className="hidden md:flex items-center gap-8">
            {isLanding && (
              <>
                <button
                  onClick={() => scrollToSection('features')}
                  className={`text-sm font-medium hover:text-indigo-400 transition-colors duration-200 ${textColor}`}
                >
                  Features
                </button>
                <button
                  onClick={() => scrollToSection('how-it-works')}
                  className={`text-sm font-medium hover:text-indigo-400 transition-colors duration-200 ${textColor}`}
                >
                  How it works
                </button>
              </>
            )}
            <Link
              to="/login"
              className={`text-sm font-medium hover:text-indigo-400 transition-colors duration-200 ${textColor}`}
            >
              Login
            </Link>
            <Link to="/signup" className="btn-primary text-sm px-4 py-2">
              Sign up
            </Link>
          </div>

          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className={`md:hidden p-2 rounded-lg hover:bg-white/10 transition-colors ${textColor}`}
            aria-label="Toggle menu"
          >
            {mobileOpen ? (
              <X className="w-6 h-6" />
            ) : (
              <Menu className="w-6 h-6" />
            )}
          </button>
        </div>
      </nav>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div className="absolute inset-0 bg-slate-900/80 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <div className="absolute right-0 top-0 h-full w-72 bg-white shadow-xl animate-slide-in-right">
            <div className="p-6 pt-20 flex flex-col gap-4">
              {isLanding && (
                <>
                  <button
                    onClick={() => scrollToSection('features')}
                    className="text-left text-sm font-medium text-slate-700 py-2 hover:text-indigo-500 transition-colors"
                  >
                    Features
                  </button>
                  <button
                    onClick={() => scrollToSection('how-it-works')}
                    className="text-left text-sm font-medium text-slate-700 py-2 hover:text-indigo-500 transition-colors"
                  >
                    How it works
                  </button>
                </>
              )}
              <Link to="/login" className="text-sm font-medium text-slate-700 py-2 hover:text-indigo-500 transition-colors">
                Login
              </Link>
              <Link to="/signup" className="btn-primary text-center mt-2">
                Sign up
              </Link>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
