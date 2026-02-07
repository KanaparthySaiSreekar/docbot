import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Activity, Menu, X } from 'lucide-react';
import { cn } from '@/lib/cn';

const navLinks = [
  { label: 'Features', href: '/#features' },
  { label: 'How It Works', href: '/#how-it-works' },
  { label: 'About', to: '/about' },
];

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 260, damping: 24, delay: 0.1 }}
      className={cn(
        'fixed top-0 left-0 right-0 z-50 transition-all duration-500',
        scrolled ? 'top-3 left-4 right-4' : '',
      )}
    >
      <div
        className={cn(
          'transition-all duration-500',
          scrolled
            ? 'mx-auto max-w-5xl rounded-2xl bg-white/60 backdrop-blur-2xl border border-white/40 shadow-[0_8px_40px_rgba(0,0,0,0.08),inset_0_1px_0_rgba(255,255,255,0.6)]'
            : 'bg-white/30 backdrop-blur-md border-b border-white/20',
        )}
      >
        <div className={cn(
          'flex items-center justify-between transition-all duration-500',
          scrolled ? 'px-5 py-2.5 max-w-5xl mx-auto' : 'px-6 py-4 max-w-7xl mx-auto',
        )}>
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="relative">
              <div className="w-9 h-9 rounded-xl gradient-primary flex items-center justify-center transition-transform duration-300 group-hover:scale-110 group-hover:rotate-3">
                <Activity className="w-5 h-5 text-white" />
              </div>
              <div className="absolute inset-0 rounded-xl gradient-primary opacity-0 group-hover:opacity-40 blur-lg transition-opacity duration-300" />
            </div>
            <span className="font-display font-bold text-xl text-clinical-800 transition-colors duration-300 group-hover:text-primary-700">
              DocBot
            </span>
          </Link>

          {/* Desktop nav links */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map(link => {
              const common = cn(
                'relative px-4 py-2 text-sm font-medium rounded-xl transition-all duration-300',
                'text-clinical-600 hover:text-primary-700 hover:bg-primary-50/60',
              );
              return link.to ? (
                <Link key={link.label} to={link.to} className={common}>
                  {link.label}
                </Link>
              ) : (
                <a key={link.label} href={link.href} className={common}>
                  {link.label}
                </a>
              );
            })}
          </div>

          {/* Right side */}
          <div className="flex items-center gap-3">
            <Link
              to="/login"
              className="hidden md:inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-xl bg-primary-500/10 text-primary-700 border border-primary-200/50 hover:bg-primary-500/20 hover:border-primary-300/60 transition-all duration-300"
            >
              Doctor Portal
            </Link>

            {/* Mobile menu toggle */}
            <button
              onClick={() => setMobileOpen(v => !v)}
              className="md:hidden p-2 rounded-xl text-clinical-600 hover:bg-clinical-100/60 transition-colors duration-200"
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile dropdown */}
        <motion.div
          initial={false}
          animate={mobileOpen ? { height: 'auto', opacity: 1 } : { height: 0, opacity: 0 }}
          transition={{ type: 'spring', stiffness: 300, damping: 28 }}
          className="md:hidden overflow-hidden"
        >
          <div className="px-5 pb-4 pt-1 flex flex-col gap-1 border-t border-white/20">
            {navLinks.map(link => {
              const common = 'block px-4 py-2.5 text-sm font-medium rounded-xl text-clinical-600 hover:text-primary-700 hover:bg-primary-50/60 transition-all duration-200';
              return link.to ? (
                <Link key={link.label} to={link.to} className={common} onClick={() => setMobileOpen(false)}>
                  {link.label}
                </Link>
              ) : (
                <a key={link.label} href={link.href} className={common} onClick={() => setMobileOpen(false)}>
                  {link.label}
                </a>
              );
            })}
            <Link
              to="/login"
              className="block px-4 py-2.5 text-sm font-medium rounded-xl bg-primary-500/10 text-primary-700 hover:bg-primary-500/20 transition-all duration-200 mt-1"
              onClick={() => setMobileOpen(false)}
            >
              Doctor Portal
            </Link>
          </div>
        </motion.div>
      </div>
    </motion.nav>
  );
}
