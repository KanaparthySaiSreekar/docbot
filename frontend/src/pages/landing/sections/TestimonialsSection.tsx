import { Star } from 'lucide-react';
import { motion, useReducedMotion } from 'framer-motion';
import { ScrollReveal } from '@/components/motion/ScrollReveal';
import { blurFocus, wideStaggerContainer, flipIn } from '@/lib/animations';

const testimonials = [
  {
    name: 'Lakshmi Kumari',
    content: 'With all your great medications, I am almost normal and got a very good relief from Rheumatoid arthritis. Thank you very much for your great treatment.',
    rating: 5,
  },
  {
    name: 'Murali Ammigalla',
    content: 'Took treatment for several years elsewhere but none of them succeeded. Then I came to Dr. Alivelu and took Homoeopathy treatment. To my surprise, my wife conceived within 2 months of her treatment. We are very happy and grateful!',
    rating: 5,
  },
  {
    name: 'Jayalalitha Kadam',
    content: 'Dr. Alivelu is an excellent homoeopathy doctor. She listens to complaints very patiently and counsels about the condition in a very simple way. I was diagnosed with PCOS having irregular menses — after her treatment, the cyst disappeared and menses became regular.',
    rating: 5,
  },
  {
    name: 'Srimayee P.',
    content: 'I had been struggling with sinus for years and tried many treatments without success. Doctor took the time to understand my concerns, explained the treatment plan in detail, and prescribed remedies tailored to my needs. The results have been remarkable!',
    rating: 5,
  },
  {
    name: 'Leena Hari',
    content: 'I reached out to Dr. Alivelu for my long-standing migraine, which had been bothering me for years. She listened to my symptoms with great care, and her treatment was amazing. I feel much better now and have been able to overcome it.',
    rating: 5,
  },
  {
    name: 'Satish Gopal',
    content: 'I have been taking medicine from Dr. Alivelu for the past year and there has been considerable improvement. She spends a lot of time going to the root cause of the problem to give an effective medicine. I would highly recommend her.',
    rating: 5,
  },
];

export function TestimonialsSection() {
  const prefersReducedMotion = useReducedMotion();

  return (
    <section id="testimonials" className="py-24 relative overflow-hidden">
      <div className="max-w-7xl mx-auto px-6 relative">
        <ScrollReveal variants={blurFocus} className="text-center mb-16">
          <h2 className="text-4xl font-display font-bold text-clinical-800 mb-4">
            What Our Patients Say
          </h2>
          <p className="text-lg text-clinical-500 max-w-2xl mx-auto">
            Real reviews from our patients on Google.
          </p>
        </ScrollReveal>

        {prefersReducedMotion ? (
          <div className="grid md:grid-cols-3 gap-6">
            {testimonials.map(({ name, content, rating }) => (
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
                    <p className="text-xs text-clinical-400">Patient</p>
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
            {testimonials.map(({ name, content, rating }) => (
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
                      <p className="text-xs text-clinical-400">Patient</p>
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
