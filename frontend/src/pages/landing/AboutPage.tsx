import { MapPin, Clock, Phone, Award, GraduationCap, MessageSquare } from 'lucide-react';
import { motion } from 'framer-motion';
import { Navbar } from './sections/Navbar';
import { FooterSection } from './sections/FooterSection';
import { ScrollReveal } from '@/components/motion/ScrollReveal';
import { slideUp, slideInLeft, slideInRight, fadeIn } from '@/lib/animations';

const qualifications = [
  'MBBS — All India Institute of Medical Sciences, New Delhi',
  'MD (General Medicine) — AIIMS, New Delhi',
  '15+ years of clinical practice',
  'Member, Indian Medical Association',
];

export default function AboutPage() {
  return (
    <div className="min-h-screen">
      <Navbar />

      {/* Hero header */}
      <section className="gradient-hero pt-32 pb-20 relative overflow-hidden">
        <div className="orb orb-teal w-[400px] h-[400px] top-10 -right-32" />
        <div className="orb orb-blue w-[300px] h-[300px] -bottom-20 left-10" />

        <div className="max-w-4xl mx-auto px-6 text-center relative">
          <motion.div
            variants={slideUp}
            initial="hidden"
            animate="visible"
          >
            <div className="w-24 h-24 rounded-3xl gradient-primary flex items-center justify-center mx-auto mb-6 shadow-lg">
              <GraduationCap className="w-12 h-12 text-white" />
            </div>
            <h1 className="text-4xl lg:text-5xl font-display font-extrabold text-clinical-800 mb-4">
              Dr. Sai Sreekar
            </h1>
            <p className="text-xl text-clinical-500 font-medium">
              General Medicine & Digital Healthcare
            </p>
          </motion.div>
        </div>
      </section>

      {/* About section */}
      <section className="py-20 bg-gradient-to-b from-white to-primary-50/20">
        <div className="max-w-4xl mx-auto px-6">
          <div className="grid md:grid-cols-2 gap-12 items-start">
            <ScrollReveal variants={slideInLeft}>
              <h2 className="text-3xl font-display font-bold text-clinical-800 mb-6">
                About Me
              </h2>
              <div className="space-y-4 text-clinical-600 leading-relaxed">
                <p>
                  With over 15 years of experience in general medicine, I am passionate about
                  making healthcare accessible and convenient for everyone. My practice combines
                  traditional clinical expertise with modern digital tools.
                </p>
                <p>
                  I believe that technology should empower patients — from easy WhatsApp-based
                  booking to secure digital prescriptions. That's why I built DocBot: to bridge
                  the gap between quality healthcare and convenience.
                </p>
              </div>
            </ScrollReveal>

            <ScrollReveal variants={slideInRight}>
              <h3 className="text-lg font-display font-semibold text-clinical-800 mb-4 flex items-center gap-2">
                <Award className="w-5 h-5 text-primary-600" />
                Qualifications
              </h3>
              <ul className="space-y-3">
                {qualifications.map((q) => (
                  <li key={q} className="flex items-start gap-3 text-clinical-600">
                    <div className="w-2 h-2 rounded-full bg-primary-400 mt-2 shrink-0" />
                    {q}
                  </li>
                ))}
              </ul>
            </ScrollReveal>
          </div>
        </div>
      </section>

      {/* Clinic section */}
      <section className="py-20 bg-gradient-to-b from-primary-50/20 to-white">
        <div className="max-w-4xl mx-auto px-6">
          <ScrollReveal className="text-center mb-12">
            <h2 className="text-3xl font-display font-bold text-clinical-800 mb-4">
              Visit the Clinic
            </h2>
            <p className="text-clinical-500">
              In-person consultations are available at the following location.
            </p>
          </ScrollReveal>

          <div className="grid md:grid-cols-3 gap-6">
            <ScrollReveal variants={slideUp}>
              <div className="glass-card p-6 text-center h-full">
                <div className="w-12 h-12 rounded-xl bg-primary-100 text-primary-600 flex items-center justify-center mx-auto mb-4">
                  <MapPin className="w-6 h-6" />
                </div>
                <h3 className="font-display font-semibold text-clinical-800 mb-2">Address</h3>
                <p className="text-sm text-clinical-500">
                  123 Health Avenue, Jubilee Hills<br />
                  Hyderabad, Telangana 500033
                </p>
              </div>
            </ScrollReveal>

            <ScrollReveal variants={slideUp}>
              <div className="glass-card p-6 text-center h-full">
                <div className="w-12 h-12 rounded-xl bg-accent-100 text-accent-600 flex items-center justify-center mx-auto mb-4">
                  <Clock className="w-6 h-6" />
                </div>
                <h3 className="font-display font-semibold text-clinical-800 mb-2">Hours</h3>
                <p className="text-sm text-clinical-500">
                  Mon — Sat: 9:00 AM — 7:00 PM<br />
                  Sunday: By appointment only
                </p>
              </div>
            </ScrollReveal>

            <ScrollReveal variants={slideUp}>
              <div className="glass-card p-6 text-center h-full">
                <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-4">
                  <Phone className="w-6 h-6" />
                </div>
                <h3 className="font-display font-semibold text-clinical-800 mb-2">Contact</h3>
                <p className="text-sm text-clinical-500">
                  +91 98765 43210<br />
                  doctor@docbot.health
                </p>
              </div>
            </ScrollReveal>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 bg-white">
        <div className="max-w-2xl mx-auto px-6">
          <ScrollReveal variants={fadeIn}>
            <div className="gradient-accent rounded-3xl p-10 text-center relative overflow-hidden">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_50%,rgba(255,255,255,0.12),transparent)] pointer-events-none" />
              <MessageSquare className="w-10 h-10 text-white/80 mx-auto mb-4 relative" />
              <h2 className="text-2xl font-display font-bold text-white mb-3 relative">
                Book via WhatsApp
              </h2>
              <p className="text-white/80 mb-6 relative">
                The fastest way to book an appointment. Just send a message!
              </p>
              <a
                href="https://wa.me/919876543210"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 bg-white text-primary-700 font-medium px-6 py-3 rounded-xl shadow-lg hover:bg-clinical-50 transition-colors relative"
              >
                Open WhatsApp
              </a>
            </div>
          </ScrollReveal>
        </div>
      </section>

      <FooterSection />
    </div>
  );
}
