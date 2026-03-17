import { motion } from 'framer-motion';
import { ArrowRight, Play } from 'lucide-react';
import { Button } from './ui/button';
import { trackEvent, EVENTS } from '../lib/analytics';

export const HeroSection = ({ onRegisterClick }) => {
  const handleDownloadClick = () => {
    trackEvent(EVENTS.HERO_CTA_CLICK, { button: 'descargar' });
  };

  const handleDemoClick = () => {
    trackEvent(EVENTS.DEMO_CLICK);
    const demoSection = document.getElementById('como-funciona');
    if (demoSection) {
      demoSection.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <section 
      className="min-h-screen relative cosmic-bg pt-24 lg:pt-32 pb-16 overflow-hidden"
      data-testid="hero-section"
    >
      {/* Background decoration */}
      <div className="absolute inset-0 geometric-grid opacity-30" />
      
      {/* Floating geometric shapes */}
      <motion.div
        className="absolute top-1/4 right-1/4 w-32 h-32 border border-[#3B82F6]/30 rotate-45"
        animate={{ 
          rotate: [45, 90, 45],
          scale: [1, 1.1, 1]
        }}
        transition={{ duration: 8, repeat: Infinity, ease: "easeInOut" }}
      />
      <motion.div
        className="absolute bottom-1/3 left-1/5 w-24 h-24 border border-[#FACC15]/20 rounded-full"
        animate={{ 
          y: [0, -20, 0],
          opacity: [0.3, 0.6, 0.3]
        }}
        transition={{ duration: 6, repeat: Infinity, ease: "easeInOut" }}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
          {/* Text Content */}
          <motion.div
            initial={{ opacity: 0, x: -50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            className="text-left"
          >
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="inline-flex items-center gap-2 px-4 py-2 bg-zinc-900/80 border border-zinc-800 rounded-full mb-6"
            >
              <span className="w-2 h-2 bg-[#FACC15] rounded-full animate-pulse" />
              <span className="text-sm text-zinc-400">$200 MXN/mes · 12 dominios profesionales</span>
            </motion.div>

            <h1 className="font-mono text-4xl sm:text-5xl lg:text-6xl font-bold text-white leading-tight mb-6">
              Tu operación,{' '}
              <span className="text-[#FACC15] text-glow-yellow">tu modelo</span>
            </h1>

            <p className="text-lg sm:text-xl text-zinc-400 mb-8 max-w-xl leading-relaxed">
              Un aprendiz que observa cómo trabajas y se ajusta a tu forma de decidir
            </p>

            <div className="flex flex-col sm:flex-row gap-4 mb-8">
              <Button
                size="lg"
                onClick={handleDownloadClick}
                className="bg-[#FACC15] text-black hover:bg-[#FDE047] font-semibold text-lg px-8 py-6 glow-yellow"
                data-testid="hero-download-btn"
              >
                Descargar App
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
              <Button
                size="lg"
                variant="outline"
                onClick={handleDemoClick}
                className="border-zinc-700 text-white hover:bg-zinc-900 hover:border-[#3B82F6] font-semibold text-lg px-8 py-6"
                data-testid="hero-demo-btn"
              >
                <Play className="mr-2 h-5 w-5" />
                Ver cómo funciona
              </Button>
            </div>

            {/* Trust badges */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6 }}
              className="flex items-center gap-6 text-sm text-zinc-500"
            >
              <div className="flex items-center gap-2">
                <span className="text-[#3B82F6]">●</span>
                Privacidad primero
              </div>
              <div className="flex items-center gap-2">
                <span className="text-[#FACC15]">●</span>
                Tu modelo descargable
              </div>
            </motion.div>
          </motion.div>

          {/* Visual/Mockup */}
          <motion.div
            initial={{ opacity: 0, x: 50 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="relative"
          >
            <div className="mockup-frame p-1">
              <div className="bg-[#09090B] rounded-lg overflow-hidden">
                {/* Mockup header */}
                <div className="flex items-center gap-2 px-4 py-3 border-b border-zinc-800">
                  <div className="flex gap-1.5">
                    <div className="w-3 h-3 rounded-full bg-red-500/80" />
                    <div className="w-3 h-3 rounded-full bg-yellow-500/80" />
                    <div className="w-3 h-3 rounded-full bg-green-500/80" />
                  </div>
                  <span className="text-xs text-zinc-500 ml-2 font-mono">mileforum — aprendiz</span>
                </div>
                
                {/* Mockup content */}
                <div className="p-6 space-y-4">
                  <div className="flex items-start gap-4">
                    <div className="w-10 h-10 rounded-lg bg-[#3B82F6]/20 flex items-center justify-center">
                      <div className="w-6 h-6 rounded border-2 border-[#3B82F6]" />
                    </div>
                    <div className="flex-1">
                      <div className="h-4 bg-zinc-800 rounded w-3/4 mb-2" />
                      <div className="h-3 bg-zinc-800/50 rounded w-1/2" />
                    </div>
                  </div>
                  
                  <div className="p-4 border border-[#FACC15]/30 rounded-lg bg-[#FACC15]/5">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-xs font-mono text-[#FACC15]">SUGERENCIA</span>
                    </div>
                    <div className="h-3 bg-zinc-700 rounded w-full mb-2" />
                    <div className="h-3 bg-zinc-700 rounded w-4/5" />
                  </div>

                  <div className="flex gap-2">
                    <div className="px-4 py-2 bg-[#FACC15] text-black text-sm rounded font-medium">
                      Confirmar
                    </div>
                    <div className="px-4 py-2 border border-zinc-700 text-sm rounded text-zinc-400">
                      Corregir
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Floating badge */}
            <motion.div
              className="absolute -bottom-4 -left-4 px-4 py-2 bg-zinc-900 border border-zinc-800 rounded-lg shadow-xl floating-badge"
              animate={{ y: [0, -8, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
            >
              <span className="text-sm font-mono">
                <span className="text-[#3B82F6]">+2,847</span>{' '}
                <span className="text-zinc-500">episodios procesados</span>
              </span>
            </motion.div>
          </motion.div>
        </div>
      </div>
    </section>
  );
};
