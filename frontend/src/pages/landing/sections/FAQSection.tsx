import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown } from 'lucide-react';
import { ScrollReveal } from '@/components/motion/ScrollReveal';
import { blurFocus, staggerContainer, staggerItem } from '@/lib/animations';
import { cn } from '@/lib/cn';

const faqs = [
  {
    question: 'What is Homeopathy?',
    answer:
      'Homeopathy is a natural system of medicine that uses highly diluted substances to stimulate the body\'s own healing mechanisms. It treats the person as a whole — considering physical, mental, and emotional well-being — rather than just addressing isolated symptoms.',
  },
  {
    question: 'Is Homeopathy safe?',
    answer:
      'Yes, homeopathic medicines are completely safe and non-toxic. They are prepared from natural substances and are highly diluted, making them free from harmful side effects. They are safe for people of all ages, including infants, pregnant women, and the elderly.',
  },
  {
    question: 'How long does Homeopathy treatment take to show results?',
    answer:
      'The duration varies depending on the condition. Acute illnesses like colds or fevers can improve within hours to days. Chronic conditions such as skin disorders, allergies, or hormonal imbalances may take a few weeks to months. Dr. Alivelu will provide a clear treatment timeline during your consultation.',
  },
  {
    question: 'Can Homeopathy be taken alongside other medications?',
    answer:
      'Yes, homeopathic medicines can generally be taken alongside conventional medicines without any interactions. However, it is always recommended to inform your doctor about all medications you are currently taking so treatment can be coordinated effectively.',
  },
  {
    question: 'What conditions can Homeopathy treat?',
    answer:
      'Homeopathy can treat a wide range of conditions including allergies, skin disorders (eczema, psoriasis), respiratory issues, digestive problems, hormonal imbalances (PCOS, thyroid), migraines, arthritis, stress, anxiety, and many more. It is especially effective for chronic and recurring conditions.',
  },
  {
    question: 'How do I book an appointment?',
    answer:
      'You can book an appointment easily through WhatsApp by clicking the green button on this page, or call us directly at +91 99632 99060. You can also fill out the booking form in the Contact Us section above. We offer both in-clinic and online consultations.',
  },
  {
    question: 'Do you offer online consultations?',
    answer:
      'Yes, we offer online video consultations for patients who cannot visit the clinic in person. You will receive the same thorough consultation, and medicines can be couriered to your address. Book via WhatsApp or phone to schedule an online appointment.',
  },
  {
    question: 'Are there any dietary restrictions during Homeopathy treatment?',
    answer:
      'Generally, it is advised to avoid strong flavors like coffee, raw onion, garlic, and mint close to the time of taking your medicine, as they may reduce its effectiveness. Dr. Alivelu will provide specific dietary guidance based on your individual treatment plan.',
  },
];

function FAQItem({ question, answer }: { question: string; answer: string }) {
  const [open, setOpen] = useState(false);

  return (
    <motion.div variants={staggerItem}>
      <button
        onClick={() => setOpen((v) => !v)}
        className={cn(
          'w-full text-left glass-card rounded-2xl p-5 transition-all duration-300',
          open && 'ring-1 ring-primary-200/60',
        )}
      >
        <div className="flex items-center justify-between gap-4">
          <h3 className="text-base font-semibold text-clinical-800">{question}</h3>
          <motion.div
            animate={{ rotate: open ? 180 : 0 }}
            transition={{ duration: 0.3 }}
            className="shrink-0"
          >
            <ChevronDown className="w-5 h-5 text-primary-500" />
          </motion.div>
        </div>
        <AnimatePresence initial={false}>
          {open && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
              className="overflow-hidden"
            >
              <p className="text-clinical-500 leading-relaxed mt-3 pt-3 border-t border-clinical-100/60">
                {answer}
              </p>
            </motion.div>
          )}
        </AnimatePresence>
      </button>
    </motion.div>
  );
}

export function FAQSection() {
  return (
    <section id="faq" className="py-24 relative overflow-hidden">
      <div className="max-w-3xl mx-auto px-6">
        <ScrollReveal variants={blurFocus} className="text-center mb-16">
          <p className="text-sm font-semibold uppercase tracking-widest text-primary-500 mb-3">
            FAQs
          </p>
          <h2 className="text-4xl font-display font-bold text-clinical-800 mb-4">
            Frequently Asked Questions
          </h2>
          <p className="text-lg text-clinical-500 max-w-2xl mx-auto">
            Everything you need to know about homeopathy and our treatments.
          </p>
        </ScrollReveal>

        <motion.div
          className="space-y-3"
          variants={staggerContainer}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-80px' }}
        >
          {faqs.map((faq) => (
            <FAQItem key={faq.question} {...faq} />
          ))}
        </motion.div>
      </div>
    </section>
  );
}
