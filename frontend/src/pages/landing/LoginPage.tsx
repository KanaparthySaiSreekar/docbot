import { Link } from 'react-router-dom';
import { Stethoscope, ArrowLeft } from 'lucide-react';
import { motion } from 'framer-motion';
import { Button } from '@/components/ui/Button';
import { fadeIn, scaleIn } from '@/lib/animations';

export default function LoginPage() {
  return (
    <div className="min-h-screen gradient-hero flex items-center justify-center px-6 relative overflow-hidden">
      {/* Decorative orbs */}
      <div className="orb orb-teal w-[500px] h-[500px] -top-40 -right-40" />
      <div className="orb orb-blue w-[400px] h-[400px] -bottom-32 -left-32" />

      <motion.div
        variants={scaleIn}
        initial="hidden"
        animate="visible"
        className="w-full max-w-md relative"
      >
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-sm text-clinical-500 hover:text-clinical-700 transition-colors mb-8"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to home
        </Link>

        <div className="glass-card p-10 text-center">
          <motion.div
            variants={fadeIn}
            initial="hidden"
            animate="visible"
            className="w-16 h-16 rounded-2xl gradient-primary flex items-center justify-center mx-auto mb-6"
          >
            <Stethoscope className="w-8 h-8 text-white" />
          </motion.div>

          <h1 className="text-2xl font-display font-bold text-clinical-800 mb-2">
            Doctor Portal
          </h1>
          <p className="text-clinical-500 mb-8">
            Sign in to manage your practice, appointments, and prescriptions.
          </p>

          <a href="/auth/login" className="block">
            <Button size="lg" className="w-full text-base">
              <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                <path
                  fill="currentColor"
                  d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z"
                />
                <path
                  fill="currentColor"
                  d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                />
                <path
                  fill="currentColor"
                  d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                />
                <path
                  fill="currentColor"
                  d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                />
              </svg>
              Sign in with Google
            </Button>
          </a>

          <p className="text-xs text-clinical-400 mt-6">
            Secure authentication powered by Google OAuth 2.0
          </p>
        </div>
      </motion.div>
    </div>
  );
}
