import { motion } from 'framer-motion';
import { Sparkles, GitBranch, Activity, MessageCircle, ArrowRight } from 'lucide-react';
import { Button } from './ui/button';
import { trackEvent, EVENTS } from '../lib/analytics';

export const RoadmapSection = () => {
  const fase2Features = [
    {
      icon: GitBranch,
      title: 'Grafos operativos',
    },
    {
      icon: Activity,
      title: 'Simulación de escenarios',
    },
    {
      icon: MessageCircle,
      title: 'Agente conversacional nativo',
    }
  ];

  const handleMoreInfoClick = () => {
    trackEvent(EVENTS.FASE2_CLICK);
  };

  return (
    <section 
      id="roadmap" 
      className="py-24 lg:py-32 cosmic-bg relative overflow-hidden"
      data-testid="roadmap-section"
    >
      {/* Decorative elements */}
      <motion.div
        className="absolute top-20 right-10 w-64 h-64 rounded-full"
        style={{
          background: 'radial-gradient(circle, rgba(59, 130, 246, 0.1) 0%, transparent 70%)'
        }}
        animate={{
          scale: [1, 1.2, 1],
          opacity: [0.5, 0.8, 0.5]
        }}
        transition={{ duration: 8, repeat: Infinity }}
      />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="max-w-2xl mx-auto text-center"
        >
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-[#3B82F6]/10 border border-[#3B82F6]/30 rounded-full mb-6">
            <Sparkles className="w-4 h-4 text-[#3B82F6]" />
            <span className="text-sm font-mono text-[#3B82F6]">En desarrollo</span>
          </div>

          <h2 className="font-mono text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-6">
            Fase 2: <span className="text-gradient-blue">Habitabilidad</span>
          </h2>

          <p className="text-xl text-zinc-400 mb-12 italic">
            "Cuando tu operación sea clara,<br />
            llegarán herramientas para hacerla habitable."
          </p>

          <div className="grid sm:grid-cols-3 gap-6 mb-10">
            {fase2Features.map((feature, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                className="flex flex-col items-center gap-3 p-4"
                data-testid={`fase2-feature-${index}`}
              >
                <div className="w-12 h-12 rounded-lg bg-[#3B82F6]/10 border border-[#3B82F6]/30 flex items-center justify-center">
                  <feature.icon className="w-6 h-6 text-[#3B82F6]" />
                </div>
                <span className="text-zinc-400 text-sm text-center">
                  {feature.title}
                </span>
              </motion.div>
            ))}
          </div>

          <Button
            variant="outline"
            onClick={handleMoreInfoClick}
            className="border-[#3B82F6]/50 text-[#3B82F6] hover:bg-[#3B82F6]/10 hover:border-[#3B82F6]"
            data-testid="fase2-more-info-btn"
          >
            Más información
            <ArrowRight className="ml-2 w-4 h-4" />
          </Button>
        </motion.div>
      </div>
    </section>
  );
};
