import { useEffect, useRef, useState } from 'react';
import { motion, useInView } from 'framer-motion';
import { Users, Star, FileText, Clock } from 'lucide-react';
import { clipReveal } from '@/lib/animations';

const stats = [
  { icon: Users, value: 500, suffix: '+', label: 'Patients' },
  { icon: Star, value: 4.9, suffix: '', label: 'Rating', decimals: 1 },
  { icon: FileText, value: 10000, suffix: '+', label: 'Prescriptions' },
  { icon: Clock, value: 24, suffix: '/7', label: 'Available' },
];

function AnimatedCounter({
  value,
  suffix,
  decimals = 0,
}: {
  value: number;
  suffix: string;
  decimals?: number;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true });
  const [display, setDisplay] = useState('0');

  useEffect(() => {
    if (!inView) return;

    const duration = 1500;
    const start = performance.now();

    function tick(now: number) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = eased * value;

      if (decimals > 0) {
        setDisplay(current.toFixed(decimals));
      } else {
        setDisplay(Math.floor(current).toLocaleString());
      }

      if (progress < 1) {
        requestAnimationFrame(tick);
      }
    }

    requestAnimationFrame(tick);
  }, [inView, value, decimals]);

  return (
    <span ref={ref}>
      {display}
      {suffix}
    </span>
  );
}

export function StatsSection() {
  return (
    <section className="py-16 relative overflow-hidden">
      <motion.div
        variants={clipReveal}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true }}
        className="mx-4 lg:mx-auto lg:max-w-6xl rounded-3xl bg-gradient-to-r from-primary-600 via-accent-600 to-primary-700 relative overflow-hidden"
      >
        {/* Pattern overlay */}
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_50%,rgba(255,255,255,0.08),transparent),radial-gradient(circle_at_80%_50%,rgba(255,255,255,0.06),transparent)] pointer-events-none" />

        <div className="px-6 py-12">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map(({ icon: Icon, value, suffix, label, decimals }) => (
              <div key={label} className="text-center">
                <Icon className="w-7 h-7 text-white/60 mx-auto mb-3" />
                <div className="text-3xl lg:text-4xl font-display font-extrabold text-white mb-1">
                  <AnimatedCounter value={value} suffix={suffix} decimals={decimals} />
                </div>
                <div className="text-sm text-white/70 font-medium">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </motion.div>
    </section>
  );
}
