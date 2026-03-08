import { Award, Clock, Phone, MapPin } from 'lucide-react';
import { ScrollReveal } from '@/components/motion/ScrollReveal';
import { slideInLeft, slideInRight, blurFocus } from '@/lib/animations';
import doctorImg from '@/assets/doctor1.png';

const qualifications = [
  'BHMS — Recognized Homeopathic Medical College',
  'Specialized in Classical Homeopathy',
  '25+ years of clinical practice',
  'Member, Homeopathic Medical Association of India',
];

const contactDetails = [
  {
    icon: MapPin,
    label: 'Address',
    value: 'Shop C11, Ground Floor, Nacharam - Mallapur Rd, opposite HMT Kamaan, Snehapuri Colony, Nacharam, Secunderabad, Telangana 500076',
    href: 'https://www.google.com/maps/place/ShivaPuja+Homeo+Store+%26+Clinic/@17.4245071,78.5443992,17z/data=!3m1!4b1!4m6!3m5!1s0x3bcb995c391b668f:0x5404f43ac4527dc!8m2!3d17.4245071!4d78.5469741!16s%2Fg%2F1pp2xbb4c',
  },
  {
    icon: Clock,
    label: 'Hours',
    value: 'Mon — Sat: 9:00 AM — 7:00 PM\nSunday: By appointment only',
    href: undefined,
  },
  {
    icon: Phone,
    label: 'Contact',
    value: '+91 99632 99060',
    href: undefined,
  },
];

export function AboutSection() {
  return (
    <section id="about" className="py-24">
      <div className="max-w-7xl mx-auto px-6">
        <ScrollReveal variants={blurFocus} className="text-center mb-16">
          <h2 className="text-4xl font-display font-bold text-clinical-800 mb-4">
            About Us
          </h2>
          <p className="text-lg text-clinical-500 max-w-2xl mx-auto">
            Classical homeopathy with a modern, patient-first approach.
          </p>
        </ScrollReveal>

        <div className="grid md:grid-cols-2 gap-12 items-start">
          {/* Left - About the doctor */}
          <ScrollReveal variants={slideInLeft}>
            <div className="glass-card rounded-2xl p-8">
              <div className="flex justify-center mb-6">
                <img
                  src={doctorImg}
                  alt="Dr. ShivaPuja"
                  className="w-40 h-40 rounded-full object-cover ring-4 ring-primary-100"
                />
              </div>
              <h3 className="text-2xl font-display font-bold text-clinical-800 mb-4 text-center">
                Dr. ShivaPuja
              </h3>
              <div className="space-y-4 text-clinical-600 leading-relaxed mb-6">
                <p>
                  With over 15 years of experience in homeopathic medicine, Dr. ShivaPuja is
                  passionate about making healthcare accessible and convenient for everyone,
                  combining traditional clinical expertise with modern digital tools.
                </p>
                <p>
                  Technology should empower patients — from easy WhatsApp-based
                  booking to secure digital prescriptions. ShivaPuja Homeo bridges the gap
                  between quality healthcare and convenience.
                </p>
              </div>

              <h4 className="text-sm font-semibold text-clinical-800 mb-3 flex items-center gap-2">
                <Award className="w-4 h-4 text-primary-600" />
                Qualifications
              </h4>
              <ul className="space-y-2">
                {qualifications.map((q) => (
                  <li key={q} className="flex items-start gap-2.5 text-sm text-clinical-600">
                    <div className="w-1.5 h-1.5 rounded-full bg-primary-400 mt-1.5 shrink-0" />
                    {q}
                  </li>
                ))}
              </ul>
            </div>
          </ScrollReveal>

          {/* Right - Clinic details */}
          <ScrollReveal variants={slideInRight}>
            <div className="space-y-4">
              {contactDetails.map(({ icon: Icon, label, value, href }) => (
                <div key={label} className="glass-card rounded-2xl p-6 flex items-start gap-4">
                  <div className="w-10 h-10 rounded-xl bg-primary-100 text-primary-600 flex items-center justify-center shrink-0">
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-clinical-800 mb-1">{label}</h4>
                    {href ? (
                      <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-primary-600 hover:text-primary-700 underline underline-offset-2 whitespace-pre-line"
                      >
                        {value}
                      </a>
                    ) : (
                      <p className="text-sm text-clinical-600 whitespace-pre-line">{value}</p>
                    )}
                  </div>
                </div>
              ))}

              {/* Map */}
              <div className="glass-card rounded-2xl overflow-hidden">
                <iframe
                  title="Clinic Location"
                  src="https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3806.734864760362!2d78.54439917516575!3d17.424507183469006!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3bcb995c391b668f%3A0x5404f43ac4527dc!2sShivaPuja%20Homeo%20Store%20%26%20Clinic!5e0!3m2!1sen!2sin!4v1772927933019!5m2!1sen!2sin"
                  width="100%"
                  height="300"
                  style={{ border: 0 }}
                  allowFullScreen
                  loading="lazy"
                  referrerPolicy="no-referrer-when-downgrade"
                />
              </div>
            </div>
          </ScrollReveal>
        </div>
      </div>
    </section>
  );
}
