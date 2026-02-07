import { Star } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import { ScrollReveal } from '@/components/motion/ScrollReveal';
import { blurFocus, wideStaggerContainer, flipIn } from '@/lib/animations';

const testimonials = [
  {
    name: 'Priya S.',
    role: 'Patient',
    content: 'Booking through WhatsApp was incredibly easy. I got my appointment confirmed in under a minute! The video consultation was seamless.',
    rating: 5,
  },
  {
    name: 'Rahul M.',
    role: 'Patient',
    content: 'I love how I get my prescriptions directly on WhatsApp. No more carrying paper prescriptions to the pharmacy.',
    rating: 5,
  },
  {
    name: 'Anita K.',
    role: 'Patient',
    content: 'The online consultation feature saved me a trip to the clinic. Doctor was very thorough and the digital prescription was so convenient.',
    rating: 5,
  },
];

export function TestimonialsSection() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <section className="py-24 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 relative">
        <ScrollReveal variants={blurFocus} className="text-center mb-16">
          <h2 className="text-4xl font-display font-bold text-clinical-800 mb-4">
            Loved by Patients
          </h2>
          <p className="text-lg text-clinical-500 max-w-2xl mx-auto">
            See what our patients are saying about their experience.
          </p>
        </ScrollReveal>

        {prefersReducedMotion ? (
          <div className="grid md:grid-cols-3 gap-6">
            {testimonials.map(({ name, role, content, rating }) => (
              <div key={name} className="glass-card p-6 h-full flex flex-col">
                <div className="flex gap-1 mb-4">
                  {Array.from({ length: rating }).map((_, i) => (
                    <Star key={i} className="w-4 h-4 fill-amber-400 text-amber-400" />
                  ))}
                </div>
                <p className="text-clinical-600 leading-relaxed flex-1 mb-4">"{content}"</p>
                <div className="flex items-center gap-3 pt-4 border-t border-clinical-100/60">
                  <div className="w-10 h-10 rounded-xl bg-primary-100 flex items-center justify-center text-sm font-semibold text-primary-700">
                    {name.charAt(0)}
                  </div>
                  <div>
                    <p className="font-medium text-clinical-800">{name}</p>
                    <p className="text-xs text-clinical-400">{role}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <motion.div
            className="grid md:grid-cols-3 gap-6"
            style={{ perspective: '1200px' }}
            variants={wideStaggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-80px' }}
          >
            {testimonials.map(({ name, role, content, rating }) => (
              <motion.div key={name} variants={flipIn}>
                <div className="glass-card p-6 h-full flex flex-col">
                  <div className="flex gap-1 mb-4">
                    {Array.from({ length: rating }).map((_, i) => (
                      <Star key={i} className="w-4 h-4 fill-amber-400 text-amber-400" />
                    ))}
                  </div>
                  <p className="text-clinical-600 leading-relaxed flex-1 mb-4">"{content}"</p>
                  <div className="flex items-center gap-3 pt-4 border-t border-clinical-100/60">
                    <div className="w-10 h-10 rounded-xl bg-primary-100 flex items-center justify-center text-sm font-semibold text-primary-700">
                      {name.charAt(0)}
                    </div>
                    <div>
                      <p className="font-medium text-clinical-800">{name}</p>
                      <p className="text-xs text-clinical-400">{role}</p>
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </section>
  );
}
