import { Link } from 'react-router-dom';
import { Activity, Heart } from 'lucide-react';
import { ScrollReveal } from '@/components/motion/ScrollReveal';
import { fadeIn } from '@/lib/animations';

export function FooterSection() {
  return (
    <ScrollReveal variants={fadeIn}>
      <footer className="border-t border-clinical-100/30">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <Link to="/" className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg gradient-primary flex items-center justify-center">
                <Activity className="w-4 h-4 text-white" />
              </div>
              <span className="font-display font-bold text-clinical-800">DocBot</span>
            </Link>

            <nav className="flex items-center gap-6 text-sm text-clinical-500">
              <a href="/#features" className="hover:text-clinical-700 transition-colors">Features</a>
              <Link to="/about" className="hover:text-clinical-700 transition-colors">About</Link>
              <Link to="/login" className="hover:text-clinical-700 transition-colors">Doctor Portal</Link>
              <a href="#" className="hover:text-clinical-700 transition-colors">Privacy Policy</a>
            </nav>

            <p className="text-sm text-clinical-400 flex items-center gap-1">
              Made with <Heart className="w-3.5 h-3.5 text-red-400 fill-red-400" /> DocBot {new Date().getFullYear()}
            </p>
          </div>
        </div>
      </footer>
    </ScrollReveal>
  );
}
