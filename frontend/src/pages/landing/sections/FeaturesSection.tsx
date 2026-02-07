import { Video, Calendar, FileText, Shield } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import { ScrollReveal } from '@/components/motion/ScrollReveal';
import { blurFocus, staggerContainer, flipIn, scaleIn } from '@/lib/animations';

const features = [
  {
    icon: Video,
    title: 'Online Consultations',
    description: 'Connect with your doctor instantly via secure Google Meet video calls, right from your dashboard.',
    color: 'bg-accent-100 text-accent-600',
  },
  {
    icon: Calendar,
    title: 'Easy Booking',
    description: 'Book appointments in seconds through WhatsApp. Auto-synced with Google Calendar for reminders.',
    color: 'bg-primary-100 text-primary-600',
  },
  {
    icon: FileText,
    title: 'Digital Prescriptions',
    description: 'Receive prescriptions as secure PDFs directly on WhatsApp with instant download links.',
    color: 'bg-emerald-100 text-emerald-600',
  },
  {
    icon: Shield,
    title: 'Secure & Private',
    description: 'Your health data is encrypted end-to-end. HIPAA compliant with zero third-party data sharing.',
    color: 'bg-purple-100 text-purple-600',
  },
];

export function FeaturesSection() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <section id="features" className="py-24 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 relative">
        <ScrollReveal variants={blurFocus} className="text-center mb-16">
          <h2 className="text-4xl font-display font-bold text-clinical-800 mb-4">
            Everything You Need
          </h2>
          <p className="text-lg text-clinical-500 max-w-2xl mx-auto">
            A complete healthcare platform designed for both patients and doctors,
            with cutting-edge technology and a human touch.
          </p>
        </ScrollReveal>

        {prefersReducedMotion ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map(({ icon: Icon, title, description, color }) => (
              <div key={title} className="glass-card p-6 h-full group">
                <div className={`w-12 h-12 rounded-xl ${color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
                  <Icon className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-display font-semibold text-clinical-800 mb-2">{title}</h3>
                <p className="text-sm text-clinical-500 leading-relaxed">{description}</p>
              </div>
            ))}
          </div>
        ) : (
          <motion.div
            className="grid md:grid-cols-2 lg:grid-cols-4 gap-6"
            style={{ perspective: '1000px' }}
            variants={staggerContainer}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-80px' }}
          >
            {features.map(({ icon: Icon, title, description, color }) => (
              <motion.div key={title} variants={flipIn}>
                <div className="glass-card p-6 h-full group">
                  <motion.div
                    variants={scaleIn}
                    className={`w-12 h-12 rounded-xl ${color} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}
                  >
                    <Icon className="w-6 h-6" />
                  </motion.div>
                  <h3 className="text-lg font-display font-semibold text-clinical-800 mb-2">{title}</h3>
                  <p className="text-sm text-clinical-500 leading-relaxed">{description}</p>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </div>
    </section>
  );
}
