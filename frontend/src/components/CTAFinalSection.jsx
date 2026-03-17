import { motion } from 'framer-motion';
import { ArrowRight, Scale } from 'lucide-react';
import { Button } from './ui/button';
import { trackEvent, EVENTS } from '../lib/analytics';

export const CTAFinalSection = ({ onRegisterClick }) => {
  const handleDemoClick = () => {
    trackEvent(EVENTS.DEMO_CLICK, { source: 'cta_final' });
    // Demo would show abogado example
  };

  return (
    <section 
      id="cta-final" 
      className="py-24 lg:py-32 bg-[#09090B] relative overflow-hidden"
      data-testid="cta-final-section"
    >
      {/* Background glow */}
      <div 
        className="absolute inset-0"
        style={{
          background: 'radial-gradient(ellipse at center, rgba(250, 204, 21, 0.05) 0%, transparent 60%)'
        }}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="text-center"
        >
          <h2 className="font-mono text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-8">
            Empieza con <span className="text-[#FACC15] text-glow-yellow">Claridad</span>
          </h2>

          <p className="text-zinc-400 text-lg mb-10 max-w-xl mx-auto">
            Registrarte → Seleccionar dominio → Comenzar a trabajar con tu Aprendiz
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Button
              size="lg"
              onClick={onRegisterClick}
              className="bg-[#FACC15] text-black hover:bg-[#FDE047] font-semibold text-lg px-10 py-6 glow-yellow"
              data-testid="cta-final-register-btn"
            >
              Registrarse
              <ArrowRight className="ml-2 h-5 w-5" />
            </Button>
          </div>

          <div className="border-t border-zinc-800 pt-8">
            <p className="text-zinc-500 text-sm mb-4">
              O prueba la demo interactiva:
            </p>
            <Button
              variant="outline"
              onClick={handleDemoClick}
              className="border-zinc-700 text-zinc-400 hover:text-white hover:border-[#3B82F6]"
              data-testid="cta-final-demo-btn"
            >
              <Scale className="mr-2 h-4 w-4" />
              Ver demo de Abogado
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </motion.div>
      </div>
    </section>
  );
};
