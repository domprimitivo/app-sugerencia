import { motion } from 'framer-motion';
import { FileText, Eye, PenTool, RefreshCw } from 'lucide-react';

export const SolutionSection = () => {
  const steps = [
    {
      number: '1',
      icon: FileText,
      title: 'REGISTRAS',
      subtitle: 'tu operación diaria',
      description: 'Documentos, consultas, expedientes',
      color: '#FACC15'
    },
    {
      number: '2',
      icon: Eye,
      title: 'EL APRENDIZ',
      subtitle: 'observa y sugiere',
      description: 'Basado en TU historial, no en datos ajenos',
      color: '#3B82F6'
    },
    {
      number: '3',
      icon: PenTool,
      title: 'TÚ CORRIGES',
      subtitle: 'cuando se equivoca',
      description: 'Cada corrección lo hace más preciso',
      color: '#FACC15'
    },
    {
      number: '4',
      icon: RefreshCw,
      title: 'BIMESTRALMENTE',
      subtitle: 'se ajusta',
      description: 'Tu modelo personal, tus datos privados',
      color: '#3B82F6'
    }
  ];

  return (
    <section 
      id="solucion" 
      className="py-24 lg:py-32 relative cosmic-bg"
      data-testid="solution-section"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="mb-16"
        >
          <span className="inline-block px-4 py-1.5 bg-[#FACC15]/10 border border-[#FACC15]/30 rounded-full text-[#FACC15] text-sm font-mono mb-4">
            Mileforum Claridad
          </span>
          <h2 className="font-mono text-3xl sm:text-4xl lg:text-5xl font-bold text-white">
            Un sistema que crece contigo
          </h2>
        </motion.div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className="relative group"
              data-testid={`solution-step-${index}`}
            >
              <div className="bg-zinc-900/50 border border-zinc-800 rounded-xl p-6 h-full hover:border-zinc-700 transition-colors duration-300">
                {/* Step number */}
                <div 
                  className="w-12 h-12 rounded-lg flex items-center justify-center mb-4"
                  style={{ backgroundColor: `${step.color}15` }}
                >
                  <step.icon className="w-6 h-6" style={{ color: step.color }} />
                </div>

                {/* Content */}
                <div className="space-y-2">
                  <div className="flex items-baseline gap-2">
                    <span className="font-mono text-2xl font-bold" style={{ color: step.color }}>
                      {step.number}
                    </span>
                    <h3 className="font-mono text-lg font-bold text-white">
                      {step.title}
                    </h3>
                  </div>
                  <p className="text-zinc-400 font-medium">
                    {step.subtitle}
                  </p>
                  <p className="text-sm text-zinc-500">
                    {step.description}
                  </p>
                </div>

                {/* Connector line (hidden on mobile and last item) */}
                {index < steps.length - 1 && (
                  <div className="hidden lg:block absolute top-1/2 -right-3 w-6 h-0.5 bg-zinc-700" />
                )}
              </div>
            </motion.div>
          ))}
        </div>
      </div>
    </section>
  );
};
