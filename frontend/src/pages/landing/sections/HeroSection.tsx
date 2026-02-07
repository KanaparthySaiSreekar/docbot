import { lazy, Suspense, useState, useEffect } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { Activity } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { staggerContainer, staggerItem, blurFocus, slideInRight } from '@/lib/animations';

const Scene = lazy(() => import('@/components/3d/Scene').then(m => ({ default: m.Scene })));

function StaticFallback() {
  return (
    <div className="w-full h-full rounded-3xl bg-gradient-to-br from-primary-100 via-accent-50 to-primary-50 flex items-center justify-center">
      <div className="w-32 h-32 rounded-full bg-gradient-to-br from-primary-300 to-accent-300 animate-pulse-soft opacity-50" />
    </div>
  );
}

export function HeroSection() {
  const prefersReducedMotion = useReducedMotion();
  const [canRender3D, setCanRender3D] = useState(false);

  useEffect(() => {
    const cores = navigator.hardwareConcurrency || 2;
    setCanRender3D(cores >= 4);
  }, []);

  const Wrapper = prefersReducedMotion ? 'div' : motion.div;

  return (
    <section className="min-h-[calc(100vh-7rem)] relative overflow-hidden">
      <div className="relative max-w-7xl mx-auto px-6 pt-24 pb-20 lg:pt-28">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-8 items-start">
          {/* Left: Text content - staggered entrance */}
          <Wrapper
            {...(!prefersReducedMotion && {
              variants: staggerContainer,
              initial: 'hidden',
              animate: 'visible',
            })}
            className="space-y-6 pt-8 lg:pt-12"
          >
            <motion.div
              variants={staggerItem}
              className="inline-flex items-center gap-2 px-4 py-2 bg-primary-100/80 border border-primary-200 rounded-full text-sm text-primary-700 font-medium"
            >
              <Activity className="w-4 h-4" />
              AI-Powered Healthcare Platform
            </motion.div>

            <motion.h1
              variants={blurFocus}
              className="text-5xl lg:text-6xl xl:text-7xl font-display font-extrabold leading-[1.1]"
            >
              <span className="text-clinical-800">Your Health,</span>
              <br />
              <span className="text-gradient">Reimagined</span>
            </motion.h1>

            <motion.p
              variants={staggerItem}
              className="text-lg text-clinical-500 max-w-lg leading-relaxed"
            >
              Book appointments seamlessly, consult with doctors online, and manage your prescriptions — all in one secure, modern platform.
            </motion.p>

            <motion.div variants={staggerItem} className="flex flex-col sm:flex-row gap-4 pt-2">
              <a href="/auth/login">
                <Button size="lg" className="text-base">
                  Get Started — It's Free
                </Button>
              </a>
              <a href="#features">
                <Button variant="secondary" size="lg" className="text-base">
                  Learn More
                </Button>
              </a>
            </motion.div>

            {/* Trust indicators */}
            <motion.div
              variants={staggerItem}
              className="flex items-center gap-6 pt-4 text-sm text-clinical-400"
            >
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-emerald-400" />
                HIPAA Compliant
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-emerald-400" />
                256-bit Encryption
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-emerald-400" />
                Google Calendar Sync
              </div>
            </motion.div>
          </Wrapper>

          {/* Right: 3D DNA with edge diffusion */}
          <Wrapper
            {...(!prefersReducedMotion && {
              variants: slideInRight,
              initial: 'hidden',
              animate: 'visible',
            })}
            className="h-[500px] lg:h-[600px]"
            style={{
              maskImage: 'linear-gradient(to bottom, transparent 0%, black 15%, black 85%, transparent 100%)',
              WebkitMaskImage: 'linear-gradient(to bottom, transparent 0%, black 15%, black 85%, transparent 100%)',
            }}
          >
            {canRender3D ? (
              <Suspense fallback={<StaticFallback />}>
                <Scene className="w-full h-full" />
              </Suspense>
            ) : (
              <StaticFallback />
            )}
          </Wrapper>
        </div>
      </div>
    </section>
  );
}
