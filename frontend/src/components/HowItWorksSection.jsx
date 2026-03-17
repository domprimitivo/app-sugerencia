import { motion } from 'framer-motion';
import { FileInput, Cpu, Lightbulb, CheckCircle, RefreshCw } from 'lucide-react';

export const HowItWorksSection = () => {
  const steps = [
    {
      icon: FileInput,
      title: 'Arrastras documentos',
      description: 'Sube tus expedientes, consultas y documentos de trabajo',
    },
    {
      icon: Cpu,
      title: 'El sistema procesa',
      description: 'Análisis profundo basado en tu historial personal',
    },
    {
      icon: Lightbulb,
      title: 'Recibes sugerencia',
      description: 'Recomendaciones contextualizadas a tu forma de trabajar',
    },
    {
      icon: CheckCircle,
      title: 'Confirmas / Corriges / Abstienes',
      description: 'Tú tienes el control de cada decisión',
    },
    {
      icon: RefreshCw,
      title: 'Tu modelo aprende',
      description: 'Cada interacción mejora la precisión',
    },
  ];

  return (
    <section 
      id="como-funciona" 
      className="py-24 lg:py-32 cosmic-bg relative overflow-hidden"
      data-testid="how-it-works-section"
    >
      {/* Background decoration */}
      <div className="absolute inset-0 geometric-grid opacity-20" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="text-center mb-16"
        >
          <h2 className="font-mono text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-4">
            Cómo funciona
          </h2>
          <p className="text-zinc-400 text-lg">
            Del documento a la decisión en un flujo simple
          </p>
        </motion.div>

        {/* Flow diagram header */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="flex justify-center mb-12"
        >
          <div className="flex items-center gap-4 px-6 py-3 bg-zinc-900/80 border border-zinc-800 rounded-full">
            <span className="font-mono text-sm text-[#FACC15]">EMBUDO</span>
            <span className="text-zinc-600">→</span>
            <span className="font-mono text-sm text-[#3B82F6]">APRENDIZ</span>
            <span className="text-zinc-600">→</span>
            <span className="font-mono text-sm text-white">DECISIÓN</span>
          </div>
        </motion.div>

        {/* Steps */}
        <div className="relative max-w-3xl mx-auto">
          {/* Vertical line */}
          <div className="absolute left-8 top-0 bottom-0 w-px bg-gradient-to-b from-[#FACC15] via-[#3B82F6] to-transparent hidden md:block" />

          <div className="space-y-8">
            {steps.map((step, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -30 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="relative flex items-start gap-6"
                data-testid={`how-step-${index}`}
              >
                {/* Icon */}
                <div className="relative z-10 w-16 h-16 rounded-xl bg-zinc-900 border border-zinc-800 flex items-center justify-center flex-shrink-0">
                  <step.icon 
                    className="w-7 h-7" 
                    style={{ 
                      color: index % 2 === 0 ? '#FACC15' : '#3B82F6' 
                    }} 
                  />
                </div>

                {/* Content */}
                <div className="flex-1 pt-3">
                  <h3 className="font-mono text-lg font-bold text-white mb-1">
                    {step.title}
                  </h3>
                  <p className="text-zinc-400">
                    {step.description}
                  </p>
                </div>

                {/* Arrow connector */}
                {index < steps.length - 1 && (
                  <div className="absolute left-[31px] top-16 text-zinc-600 hidden md:block">
                    ↓
                  </div>
                )}
              </motion.div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
};
