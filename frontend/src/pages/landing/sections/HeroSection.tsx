import { lazy, Suspense, useState, useEffect } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { Phone, MessageCircle, Leaf } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { staggerContainer, staggerItem, blurFocus, slideInRight } from '@/lib/animations';
import doctorImg from '@/assets/doctor.png';

const Scene = lazy(() => import('@/components/3d/Scene').then(m => ({ default: m.Scene })));

function StaticFallback() {
  return (
    <div className="w-full h-full bg-gradient-to-br from-primary-100 via-accent-50 to-primary-50 flex items-center justify-center">
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
      {/* DNA Helix — full background, translucent */}
      <div className="absolute inset-0 z-0 opacity-[0.17] pointer-events-none [mask-image:linear-gradient(to_bottom,black_60%,transparent_100%)]">
        {canRender3D ? (
          <Suspense fallback={null}>
            <Scene className="w-full h-full" tilt basePairs={40} />
          </Suspense>
        ) : (
          <StaticFallback />
        )}
      </div>

      {/* Content layer */}
      <div className="relative z-10 max-w-7xl mx-auto px-6 pt-28 pb-20 lg:pt-32">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-8 items-center">
          {/* Left: Text content */}
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
              <Leaf className="w-4 h-4" />
              Trusted Homeopathy Care
            </motion.div>

            <motion.h1
              variants={blurFocus}
              className="text-5xl lg:text-6xl xl:text-7xl font-display font-extrabold leading-[1.1]"
            >
              <span className="text-clinical-800">Healing Naturally,</span>
              <br />
              <span className="text-gradient">Living Fully</span>
            </motion.h1>

            <motion.p
              variants={staggerItem}
              className="text-lg text-clinical-500 max-w-lg leading-relaxed"
            >
              Experience the power of natural healing with personalized homeopathy treatments. Book appointments instantly via WhatsApp, get expert consultations, and receive holistic care tailored to your unique health needs.
            </motion.p>

            <motion.div variants={staggerItem} className="flex flex-col sm:flex-row gap-4 pt-2">
              <a href="https://wa.me/919963299060" target="_blank" rel="noopener noreferrer">
                <Button size="lg" className="text-base">
                  <MessageCircle className="w-5 h-5 mr-2" />
                  Book Appointment
                </Button>
              </a>
              <a href="tel:+919963299060">
                <Button variant="secondary" size="lg" className="text-base">
                  <Phone className="w-5 h-5 mr-2" />
                  Call Now
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
                100% Natural & Safe
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-emerald-400" />
                Expert Specialists
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-emerald-400" />
                Holistic Wellness
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-emerald-400" />
                Proven Results
              </div>
            </motion.div>
          </Wrapper>

          {/* Right: Doctor photo + credentials */}
          <Wrapper
            {...(!prefersReducedMotion && {
              variants: slideInRight,
              initial: 'hidden',
              animate: 'visible',
            })}
            className="flex flex-col items-center lg:items-end"
          >
            <div className="relative">
              {/* Soft glow behind the frame */}
              <div className="absolute -inset-6 bg-gradient-to-br from-primary-300/40 via-accent-200/30 to-primary-200/40 rounded-[2rem] blur-3xl" />
              {/* Decorative ring accent */}
              <div className="absolute -inset-3 rounded-[1.75rem] bg-gradient-to-br from-primary-400/20 via-transparent to-accent-400/20" />
              {/* Card frame */}
              <div className="relative rounded-3xl bg-white/60 backdrop-blur-sm border border-white/50 shadow-[0_8px_40px_rgba(0,0,0,0.08)] p-3">
                <img
                  src={doctorImg}
                  alt="Smt Dr.Alivelu Shivapuja"
                  className="w-64 sm:w-72 lg:w-80 rounded-2xl object-cover"
                />
              </div>
              {/* Corner accent dots */}
              <div className="absolute -top-2 -right-2 w-4 h-4 rounded-full bg-gradient-to-br from-primary-400 to-primary-500 shadow-lg" />
              <div className="absolute -bottom-2 -left-2 w-3 h-3 rounded-full bg-gradient-to-br from-accent-400 to-accent-500 shadow-lg" />
            </div>
            <div className="mt-5 text-center lg:text-right">
              <h3 className="text-2xl font-display font-bold text-clinical-800">
                Smt Dr.Alivelu Shivapuja
              </h3>
              <p className="text-base text-clinical-500 mt-1.5 tracking-wide">
                BHMS, M.D.(Homoeo)
              </p>
              <p className="text-base font-medium text-primary-600 mt-1.5">
                Senior Homeopathy Specialist
              </p>
              <p className="text-sm text-clinical-400 mt-1">
                26+ Years of Excellence in Homeopathy
              </p>
            </div>
          </Wrapper>
        </div>
      </div>
    </section>
  );
}
