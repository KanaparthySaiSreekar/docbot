import { useState, useEffect } from 'react';
import { Phone, Mail, MapPin, Clock, Facebook, Instagram, Youtube } from 'lucide-react';
import { cn } from '@/lib/cn';

const INFO_BAR_HEIGHT = 40;

export { INFO_BAR_HEIGHT };

export function InfoBar() {
  const [hidden, setHidden] = useState(false);

  useEffect(() => {
    const onScroll = () => setHidden(window.scrollY > 50);
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <div
      className={cn(
        'fixed top-0 left-0 right-0 z-[60] transition-transform duration-300',
        hidden && '-translate-y-full',
      )}
    >
      <div className="gradient-primary text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 flex items-center justify-between h-10 text-xs">
          {/* Contact details */}
          <div className="flex items-center gap-1 sm:gap-4 overflow-x-auto">
            <a
              href="tel:+919963299060"
              className="flex items-center gap-1.5 hover:text-primary-200 transition-colors shrink-0"
            >
              <Phone className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">099632 99060</span>
            </a>

            <span className="hidden sm:block w-px h-4 bg-white/20" />

            <a
              href="mailto:shivapujahomoeo@gmail.com"
              className="flex items-center gap-1.5 hover:text-primary-200 transition-colors shrink-0"
            >
              <Mail className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">shivapujahomoeo@gmail.com</span>
            </a>

            <span className="hidden sm:block w-px h-4 bg-white/20" />

            <div className="flex items-center gap-1.5 shrink-0">
              <MapPin className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Nacharam, Hyderabad</span>
            </div>

            <span className="hidden sm:block w-px h-4 bg-white/20" />

            <div className="flex items-center gap-1.5 shrink-0">
              <Clock className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Evening 6:00 - 9:00 PM</span>
            </div>
          </div>

          {/* Social icons */}
          <div className="flex items-center gap-3 shrink-0 ml-4">
            <a href="#" aria-label="Facebook" className="hover:text-primary-200 hover:scale-110 transition-all">
              <Facebook className="w-4 h-4" />
            </a>
            <a href="#" aria-label="Instagram" className="hover:text-primary-200 hover:scale-110 transition-all">
              <Instagram className="w-4 h-4" />
            </a>
            <a href="#" aria-label="YouTube" className="hover:text-primary-200 hover:scale-110 transition-all">
              <Youtube className="w-4 h-4" />
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
