import { motion } from 'framer-motion';
import { Shield, Target, TrendingUp, Zap } from 'lucide-react';

export const DifferentiatorsSection = () => {
  const differentiators = [
    {
      icon: Shield,
      title: 'Privacidad primero',
      description: 'Tu modelo es TUYO. Descargable. Reentrenamiento sin guardar tus datos.',
      color: '#FACC15'
    },
    {
      icon: Target,
      title: 'Especializado, no genérico',
      description: 'Modelo para TU dominio, no uno adaptado mal a todos.',
      color: '#3B82F6'
    },
    {
      icon: TrendingUp,
      title: 'Aprende de ti, no de internet',
      description: 'Se ajusta a TU criterio profesional único.',
      color: '#FACC15'
    },
    {
      icon: Zap,
      title: 'Ligero pero denso',
      description: 'Interfaz simple, procesamiento profundo.',
      color: '#3B82F6'
    }
  ];

  return (
    <section 
      id="diferenciadores" 
      className="py-24 lg:py-32 bg-[#09090B]"
      data-testid="differentiators-section"
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
            Por qué NO es otro SaaS
          </h2>
        </motion.div>

        <div className="grid md:grid-cols-2 gap-6 max-w-4xl mx-auto">
          {differentiators.map((item, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6 hover:border-zinc-700 transition-colors duration-300"
              data-testid={`differentiator-${index}`}
            >
              <div className="flex items-start gap-4">
                <div 
                  className="w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0"
                  style={{ backgroundColor: `${item.color}15` }}
                >
                  <item.icon className="w-6 h-6" style={{ color: item.color }} />
                </div>
                <div>
                  <h3 className="font-mono text-lg font-bold text-white mb-2">
                    {item.title}
                  </h3>
                  <p className="text-zinc-400">
                    {item.description}
                  </p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Trust badge */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.5 }}
          className="flex justify-center mt-12"
        >
          <div className="inline-flex items-center gap-3 px-6 py-3 bg-zinc-900/80 border border-zinc-800 rounded-full">
            <Shield className="w-5 h-5 text-[#FACC15]" />
            <span className="font-mono text-sm text-zinc-400">
              Política Cero Datos — Recibo de destrucción certificado
            </span>
          </div>
        </motion.div>
      </div>
    </section>
  );
};
