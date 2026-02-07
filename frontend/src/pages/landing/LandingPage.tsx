import { Navbar } from './sections/Navbar';
import { HeroSection } from './sections/HeroSection';
import { FeaturesSection } from './sections/FeaturesSection';
import { StatsSection } from './sections/StatsSection';
import { HowItWorksSection } from './sections/HowItWorksSection';
import { TestimonialsSection } from './sections/TestimonialsSection';
import { CTASection } from './sections/CTASection';
import { FooterSection } from './sections/FooterSection';

export default function LandingPage() {
  return (
    <div className="min-h-screen gradient-hero relative overflow-hidden">
      {/* Full-page grid pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(0,0,0,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(0,0,0,0.02)_1px,transparent_1px)] bg-[size:60px_60px] pointer-events-none" />

      {/* Decorative orbs spread across the full page */}
      <div className="orb orb-teal w-[600px] h-[600px] -top-48 -left-48" />
      <div className="orb orb-blue w-[500px] h-[500px] top-20 -right-40" />
      <div className="orb orb-purple w-[300px] h-[300px] top-[600px] left-1/4" />
      <div className="orb orb-teal w-[400px] h-[400px] top-[1400px] -right-40" />
      <div className="orb orb-blue w-[350px] h-[350px] top-[2200px] left-1/3" />
      <div className="orb orb-purple w-[350px] h-[350px] top-[3000px] -left-32" />

      {/* All sections sit above the background */}
      <div className="relative">
        <Navbar />
        <HeroSection />
        <FeaturesSection />
        <StatsSection />
        <HowItWorksSection />
        <TestimonialsSection />
        <CTASection />
        <FooterSection />
      </div>
    </div>
  );
}
