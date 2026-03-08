import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Menu, X } from 'lucide-react';
import { Logo } from '@/components/icons/Logo';
import { cn } from '@/lib/cn';
import { INFO_BAR_HEIGHT } from './InfoBar';

const navLinks = [
  { label: 'Our Services', id: 'features' },
  { label: 'Departments', id: 'departments' },
  { label: 'Book', id: 'book' },
  { label: 'How It Works', id: 'how-it-works' },
  { label: 'Testimonials', id: 'testimonials' },
  { label: 'About Us', id: 'about' },
  { label: 'FAQs', id: 'faq' },
];

function scrollToSection(id: string, setActive: (id: string) => void) {
  setActive(id);
  const el = document.getElementById(id);
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [infoBarVisible, setInfoBarVisible] = useState(true);
  const [activeId, setActiveId] = useState<string | null>(null);

  const updateActive = useCallback(() => {
    const threshold = 150;
    let current: string | null = null;

    for (const link of navLinks) {
      const el = document.getElementById(link.id);
      if (el) {
        const rect = el.getBoundingClientRect();
        if (rect.top <= threshold) {
          current = link.id;
        }
      }
    }
    setActiveId(current);
  }, []);

  useEffect(() => {
    const onScroll = () => {
      setScrolled(window.scrollY > 50);
      setInfoBarVisible(window.scrollY <= 50);
      updateActive();
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    return () => window.removeEventListener('scroll', onScroll);
  }, [updateActive]);

  return (
    <motion.nav
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 260, damping: 24, delay: 0.1 }}
      style={{ top: scrolled ? undefined : infoBarVisible ? INFO_BAR_HEIGHT : 0 }}
      className={cn(
        'fixed left-0 right-0 z-50 transition-all duration-500',
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
                <Logo className="w-5 h-5 text-white" />
              </div>
              <div className="absolute inset-0 rounded-xl gradient-primary opacity-0 group-hover:opacity-40 blur-lg transition-opacity duration-300" />
            </div>
            <span className="font-display font-bold text-xl text-clinical-800 transition-colors duration-300 group-hover:text-primary-700">
              ShivaPuja Homeo
            </span>
          </Link>

          {/* Desktop nav links */}
          <div className="hidden md:flex items-center gap-1">
            {navLinks.map((link) => (
              <button
                key={link.label}
                onClick={() => scrollToSection(link.id, setActiveId)}
                className={cn(
                  'relative px-4 py-2 text-sm font-medium rounded-xl transition-all duration-300',
                  activeId === link.id
                    ? 'text-primary-700'
                    : 'text-clinical-600 hover:text-primary-700 hover:bg-primary-50/60',
                )}
              >
                {link.label}
                {activeId === link.id && (
                  <motion.div
                    layoutId="nav-active"
                    className="absolute inset-x-2 -bottom-0.5 h-0.5 rounded-full bg-primary-500"
                    transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                  />
                )}
              </button>
            ))}
          </div>

          {/* Right side */}
          <div className="flex items-center gap-3">
            {/* Mobile menu toggle */}
            <button
              onClick={() => setMobileOpen((v) => !v)}
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
            {navLinks.map((link) => (
              <button
                key={link.label}
                onClick={() => {
                  scrollToSection(link.id, setActiveId);
                  setMobileOpen(false);
                }}
                className={cn(
                  'block w-full text-left px-4 py-2.5 text-sm font-medium rounded-xl transition-all duration-200',
                  activeId === link.id
                    ? 'text-primary-700 bg-primary-50/60'
                    : 'text-clinical-600 hover:text-primary-700 hover:bg-primary-50/60',
                )}
              >
                {link.label}
              </button>
            ))}
          </div>
        </motion.div>
      </div>
    </motion.nav>
  );
}
