import { Wind, Heart, Brain, Baby, Flower2, Sparkles, Bone, Stethoscope } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import { ScrollReveal } from '@/components/motion/ScrollReveal';
import { blurFocus, staggerContainer, flipIn } from '@/lib/animations';

const departments = [
  {
    icon: Wind,
    count: '45+',
    title: 'Respiratory System',
    description: 'Asthma, Bronchitis, COPD, Allergic Rhinitis, Sinusitis',
    color: 'bg-sky-100 text-sky-600',
  },
  {
    icon: Heart,
    count: '25+',
    title: 'Cardiovascular',
    description: 'Hypertension, Heart Disease, Circulation Issues',
    color: 'bg-red-100 text-red-600',
  },
  {
    icon: Brain,
    count: '35+',
    title: 'Neurological',
    description: 'Migraine, Anxiety, Depression, Stress Disorders',
    color: 'bg-purple-100 text-purple-600',
  },
  {
    icon: Baby,
    count: '30+',
    title: 'Pediatric Care',
    description: 'Child Development, Growth Issues, Behavioral Problems',
    color: 'bg-amber-100 text-amber-600',
  },
  {
    icon: Flower2,
    count: '40+',
    title: "Women's Health",
    description: 'PCOS, Menstrual Disorders, Fertility Issues',
    color: 'bg-pink-100 text-pink-600',
  },
  {
    icon: Sparkles,
    count: '50+',
    title: 'Dermatology',
    description: 'Skin Conditions, Hair Loss, Allergic Reactions',
    color: 'bg-emerald-100 text-emerald-600',
  },
  {
    icon: Bone,
    count: '28+',
    title: 'Musculoskeletal',
    description: 'Arthritis, Joint Pain, Bone Disorders',
    color: 'bg-orange-100 text-orange-600',
  },
  {
    icon: Stethoscope,
    count: '60+',
    title: 'General Medicine',
    description: 'Digestive Issues, Immunity, Chronic Conditions',
    color: 'bg-primary-100 text-primary-600',
  },
];

export function DepartmentsSection() {
  const prefersReducedMotion = useReducedMotion();

  const cards = departments.map(({ icon: Icon, count, title, description, color }) => (
    <div key={title} className="glass-card p-6 h-full group">
      <div className="flex items-start gap-4">
        <div className={`w-12 h-12 rounded-xl ${color} flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform duration-300`}>
          <Icon className="w-6 h-6" />
        </div>
        <div>
          <span className="text-xs font-bold text-primary-500 tracking-wider">{count} CONDITIONS</span>
          <h3 className="text-lg font-display font-semibold text-clinical-800 mb-1">{title}</h3>
          <p className="text-sm text-clinical-500 leading-relaxed">{description}</p>
        </div>
      </div>
    </div>
  ));

  return (
    <section id="departments" className="py-24 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 relative">
        <ScrollReveal variants={blurFocus} className="text-center mb-16">
          <p className="text-sm font-semibold text-primary-500 tracking-widest uppercase mb-2">
            Departments Managed
          </p>
          <h2 className="text-4xl font-display font-bold text-clinical-800 mb-4">
            Your Healthcare Services
          </h2>
          <p className="text-lg text-clinical-500 max-w-2xl mx-auto">
            Comprehensive homeopathy treatment for 300+ diseases with natural, safe, and effective remedies
          </p>
        </ScrollReveal>

        {prefersReducedMotion ? (
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {cards}
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
            {departments.map(({ icon: Icon, count, title, description, color }) => (
              <motion.div key={title} variants={flipIn}>
                <div className="glass-card p-6 h-full group">
                  <div className="flex items-start gap-4">
                    <div className={`w-12 h-12 rounded-xl ${color} flex items-center justify-center shrink-0 group-hover:scale-110 transition-transform duration-300`}>
                      <Icon className="w-6 h-6" />
                    </div>
                    <div>
                      <span className="text-xs font-bold text-primary-500 tracking-wider">{count} CONDITIONS</span>
                      <h3 className="text-lg font-display font-semibold text-clinical-800 mb-1">{title}</h3>
                      <p className="text-sm text-clinical-500 leading-relaxed">{description}</p>
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
