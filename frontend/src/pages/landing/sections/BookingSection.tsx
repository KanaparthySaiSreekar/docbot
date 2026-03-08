import { useState } from 'react';
import type { FormEvent } from 'react';
import { MapPin } from 'lucide-react';
import { ScrollReveal } from '@/components/motion/ScrollReveal';
import { Input } from '@/components/ui/Input';
import { Button } from '@/components/ui/Button';
import { blurFocus, slideInLeft, slideInRight } from '@/lib/animations';

const CLINIC_ADDRESS =
  'Shop C11, Ground Floor, Nacharam - Mallapur Rd, opposite HMT Kamaan, Snehapuri Colony, Nacharam, Secunderabad, Telangana 500076';

const MAPS_EMBED_URL =
  'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d6981.5456013600815!2d78.54297254556859!3d17.425468776020246!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x3bcb995c391b668f%3A0x5404f43ac4527dc!2sShivaPuja%20Homeo%20Store%20%26%20Clinic!5e0!3m2!1sen!2sin!4v1772927987544!5m2!1sen!2sin';

export function BookingSection() {
  const [form, setForm] = useState({
    name: '',
    phone: '',
    email: '',
    message: '',
  });

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) {
    setForm((prev) => ({ ...prev, [e.target.name]: e.target.value }));
  }

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    console.log('Booking form submitted:', form);
  }

  return (
    <section id="book" className="py-24">
      <div className="max-w-7xl mx-auto px-6">
        <ScrollReveal variants={blurFocus} className="text-center mb-16">
          <p className="text-sm font-semibold uppercase tracking-widest text-primary-500 mb-3">
            Contact Us
          </p>
          <h2 className="text-4xl font-display font-bold text-clinical-800 mb-4">
            Ready to Start Your<br />Healing Journey?
          </h2>
          <p className="text-lg text-clinical-500 max-w-2xl mx-auto">
            Book your consultation today and take the first step towards natural healing with our expert homeopathy specialists.
          </p>
        </ScrollReveal>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Left - Map */}
          <ScrollReveal variants={slideInLeft}>
            <div className="glass-card rounded-2xl overflow-hidden h-full flex flex-col">
              <iframe
                title="Clinic Location"
                src={MAPS_EMBED_URL}
                className="w-full h-80 md:h-full min-h-[320px] rounded-t-2xl"
                allowFullScreen
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
              />
              <div className="p-4 flex items-start gap-2 text-clinical-600 text-sm">
                <MapPin className="w-4 h-4 mt-0.5 shrink-0 text-primary-500" />
                <span>{CLINIC_ADDRESS}</span>
              </div>
            </div>
          </ScrollReveal>

          {/* Right - Booking Form */}
          <ScrollReveal variants={slideInRight}>
            <div className="glass-card rounded-2xl p-8">
              <h2 className="text-2xl md:text-3xl font-display font-bold text-clinical-800 mb-6">
                Book a Consultation
              </h2>

              <form onSubmit={handleSubmit} className="space-y-4">
                <Input
                  id="name"
                  name="name"
                  label="Name"
                  placeholder="Your full name"
                  value={form.name}
                  onChange={handleChange}
                  required
                />
                <Input
                  id="phone"
                  name="phone"
                  type="tel"
                  label="Phone Number"
                  placeholder="Your phone number"
                  value={form.phone}
                  onChange={handleChange}
                  required
                />
                <Input
                  id="email"
                  name="email"
                  type="email"
                  label="Email"
                  placeholder="you@example.com"
                  value={form.email}
                  onChange={handleChange}
                  required
                />

                <div>
                  <label htmlFor="message" className="block text-sm font-medium text-clinical-600 mb-1.5">
                    Additional Message
                  </label>
                  <textarea
                    id="message"
                    name="message"
                    rows={4}
                    placeholder="Any additional details..."
                    value={form.message}
                    onChange={handleChange}
                    className="w-full px-4 py-2.5 bg-white/80 border border-clinical-200 rounded-xl text-clinical-800 placeholder:text-clinical-400 focus:outline-none focus:ring-2 focus:ring-primary-500/20 focus:border-primary-400 transition-all duration-200 resize-none"
                  />
                </div>

                <Button type="submit" variant="primary" size="lg" className="w-full">
                  Book Consultation
                </Button>
              </form>
            </div>
          </ScrollReveal>
        </div>
      </div>
    </section>
  );
}
