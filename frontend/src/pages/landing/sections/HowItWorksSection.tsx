import { MessageSquare, CalendarCheck, Stethoscope } from 'lucide-react';
import { ScrollReveal } from '@/components/motion/ScrollReveal';
import { blurFocus, slideInLeft, slideInRight, slideUp } from '@/lib/animations';

const steps = [
  {
    number: '01',
    icon: MessageSquare,
    title: 'Book via WhatsApp',
    description: 'Simply send a message to our WhatsApp bot. Choose your preferred date, time, and consultation type.',
    color: 'from-primary-500 to-primary-600',
  },
  {
    number: '02',
    icon: CalendarCheck,
    title: 'Get Confirmed',
    description: 'Receive instant confirmation with calendar invite and Google Meet link for online appointments.',
    color: 'from-accent-500 to-accent-600',
  },
  {
    number: '03',
    icon: Stethoscope,
    title: 'Consult & Receive',
    description: 'Meet your doctor online or in-person. Get your digital prescription sent directly to WhatsApp.',
    color: 'from-emerald-500 to-emerald-600',
  },
];

export function HowItWorksSection() {
  return (
    <section id="how-it-works" className="py-24 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 relative">
        <ScrollReveal variants={blurFocus} parallax className="text-center mb-16">
          <h2 className="text-4xl font-display font-bold text-clinical-800 mb-4">
            How It Works
          </h2>
          <p className="text-lg text-clinical-500 max-w-2xl mx-auto">
            Getting started is simple. Three easy steps to better healthcare.
          </p>
        </ScrollReveal>

        {/* Desktop: alternating slide-in layout */}
        <div className="hidden md:block">
          <div className="relative">
            {/* Connecting line */}
            <div className="absolute top-16 left-[20%] right-[20%] h-0.5 bg-gradient-to-r from-primary-200 via-accent-200 to-emerald-200" />

            <div className="grid md:grid-cols-3 gap-8">
              {steps.map(({ number, icon: Icon, title, description, color }, i) => (
                <ScrollReveal
                  key={number}
                  variants={i % 2 === 0 ? slideInLeft : slideInRight}
                  parallax
                  parallaxOffset={20 + i * 10}
                >
                  <div className="text-center relative">
                    <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${color} flex items-center justify-center mx-auto mb-5 shadow-lg relative z-10`}>
                      <Icon className="w-7 h-7 text-white" />
                    </div>
                    <span className="text-xs font-bold text-clinical-300 uppercase tracking-wider">Step {number}</span>
                    <h3 className="text-xl font-display font-semibold text-clinical-800 mt-2 mb-3">{title}</h3>
                    <p className="text-sm text-clinical-500 leading-relaxed max-w-xs mx-auto">{description}</p>
                  </div>
                </ScrollReveal>
              ))}
            </div>
          </div>
        </div>

        {/* Mobile: simple stacked */}
        <div className="md:hidden space-y-8">
          {steps.map(({ number, icon: Icon, title, description, color }) => (
            <ScrollReveal key={number} variants={slideUp}>
              <div className="text-center">
                <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${color} flex items-center justify-center mx-auto mb-5 shadow-lg`}>
                  <Icon className="w-7 h-7 text-white" />
                </div>
                <span className="text-xs font-bold text-clinical-300 uppercase tracking-wider">Step {number}</span>
                <h3 className="text-xl font-display font-semibold text-clinical-800 mt-2 mb-3">{title}</h3>
                <p className="text-sm text-clinical-500 leading-relaxed max-w-xs mx-auto">{description}</p>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
