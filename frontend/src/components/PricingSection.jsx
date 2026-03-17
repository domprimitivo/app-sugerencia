import { motion } from 'framer-motion';
import { Check } from 'lucide-react';
import { Button } from './ui/button';
import { trackEvent, EVENTS } from '../lib/analytics';

export const PricingSection = ({ onRegisterClick }) => {
  const features = [
    'Aprendiz especializado en tu dominio',
    'Episodios ilimitados',
    'Ajuste bimestral incluido',
    'Tu modelo es tuyo (descargable)',
    'Sesión itinerante con recibo de destrucción'
  ];

  const handlePricingCTA = () => {
    trackEvent(EVENTS.PRICING_CTA_CLICK);
    onRegisterClick();
  };

  return (
    <section 
      id="precios" 
      className="py-24 lg:py-32 bg-[#09090B]"
      data-testid="pricing-section"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="font-mono text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4">
            Precios transparentes
          </h2>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="max-w-lg mx-auto"
        >
          <div className="pricing-card rounded-2xl p-8" data-testid="pricing-card">
            {/* Phase badge */}
            <div className="inline-block px-3 py-1 bg-[#FACC15]/10 border border-[#FACC15]/30 rounded-full mb-6">
              <span className="font-mono text-sm text-[#FACC15]">Fase 1: Claridad</span>
            </div>

            {/* Price */}
            <div className="mb-8">
              <div className="flex items-baseline gap-2">
                <span className="font-mono text-5xl lg:text-6xl font-bold text-white">$200</span>
                <span className="text-zinc-400">MXN / mes</span>
              </div>
            </div>

            {/* Features */}
            <ul className="space-y-4 mb-8">
              {features.map((feature, index) => (
                <li key={index} className="flex items-start gap-3">
                  <div className="w-5 h-5 rounded-full bg-[#FACC15]/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Check className="w-3 h-3 text-[#FACC15]" />
                  </div>
                  <span className="text-zinc-300">{feature}</span>
                </li>
              ))}
            </ul>

            {/* CTA */}
            <Button
              size="lg"
              onClick={handlePricingCTA}
              className="w-full bg-[#FACC15] text-black hover:bg-[#FDE047] font-semibold text-lg py-6"
              data-testid="pricing-cta-btn"
            >
              Comenzar ahora
            </Button>

            {/* Coming soon note */}
            <p className="text-center text-zinc-500 text-sm mt-6">
              * Fase 2 (Habitabilidad) próximamente
            </p>
          </div>
        </motion.div>
      </div>
    </section>
  );
};
