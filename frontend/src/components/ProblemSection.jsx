import { motion } from 'framer-motion';
import { X } from 'lucide-react';

export const ProblemSection = () => {
  const problems = [
    {
      text: 'Software genérico que no entiende tu dominio',
      emphasis: 'genérico'
    },
    {
      text: '"IA" que te da respuestas sin contexto',
      emphasis: 'sin contexto'
    },
    {
      text: 'Cada episodio requiere empezar de cero',
      emphasis: 'de cero'
    }
  ];

  const consequences = [
    'Tu conocimiento se queda en tu cabeza',
    'No hay continuidad entre expedientes',
    'Las herramientas no aprenden de ti'
  ];

  return (
    <section 
      id="problema" 
      className="py-24 lg:py-32 relative bg-[#09090B]"
      data-testid="problem-section"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-100px" }}
          transition={{ duration: 0.6 }}
          className="max-w-3xl"
        >
          <h2 className="font-mono text-3xl sm:text-4xl lg:text-5xl font-bold text-white mb-12">
            ¿Te suena familiar?
          </h2>

          <div className="space-y-6 mb-12">
            {problems.map((problem, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                className="flex items-start gap-4"
                data-testid={`problem-item-${index}`}
              >
                <div className="mt-1 w-6 h-6 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center flex-shrink-0">
                  <X className="w-4 h-4 text-red-400" />
                </div>
                <p className="text-lg sm:text-xl text-zinc-300">
                  {problem.text}
                </p>
              </motion.div>
            ))}
          </div>

          <div className="border-l-2 border-[#3B82F6] pl-6 space-y-4">
            {consequences.map((consequence, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -10 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: 0.4 + index * 0.1 }}
                className="flex items-center gap-3"
                data-testid={`consequence-item-${index}`}
              >
                <span className="text-[#3B82F6]">→</span>
                <p className="text-zinc-400">{consequence}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </div>
    </section>
  );
};
