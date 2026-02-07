import { ArrowRight } from 'lucide-react';
import { ScrollReveal } from '@/components/motion/ScrollReveal';
import { Button } from '@/components/ui/Button';
import { clipReveal } from '@/lib/animations';

export function CTASection() {
  return (
    <section className="py-24">
      <div className="max-w-4xl mx-auto px-6">
        <ScrollReveal variants={clipReveal}>
          <div className="bg-gradient-to-br from-primary-600 via-accent-600 to-primary-700 rounded-3xl p-12 text-center relative overflow-hidden">
            {/* Background decoration */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_30%,rgba(255,255,255,0.12),transparent),radial-gradient(circle_at_80%_70%,rgba(255,255,255,0.08),transparent)] pointer-events-none" />

            <h2 className="text-3xl lg:text-4xl font-display font-bold text-white mb-4 relative">
              Ready to Get Started?
            </h2>
            <p className="text-lg text-white/80 max-w-xl mx-auto mb-8 relative">
              Join thousands of patients who have already transformed their healthcare experience.
            </p>
            <div className="relative">
              <a href="/auth/login">
                <Button
                  variant="secondary"
                  size="lg"
                  className="bg-white text-primary-700 hover:bg-clinical-50 border-transparent text-base shadow-lg"
                >
                  Sign in with Google
                  <ArrowRight className="w-4 h-4 ml-2" />
                </Button>
              </a>
            </div>
          </div>
        </ScrollReveal>
      </div>
    </section>
  );
}
