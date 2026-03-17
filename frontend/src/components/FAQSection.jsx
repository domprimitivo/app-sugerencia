import { motion } from 'framer-motion';
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from './ui/accordion';
import { trackEvent, EVENTS } from '../lib/analytics';

export const FAQSection = () => {
  const faqs = [
    {
      question: '¿Es otro chatbot?',
      answer: 'No. Es un sistema que aprende tu OPERACIÓN, no que responde preguntas genéricas. El Aprendiz observa cómo trabajas y adapta sus sugerencias a tu forma de decidir.'
    },
    {
      question: '¿Mis datos están seguros?',
      answer: 'Sí. Reentrenamiento sin persistencia. Descargas recibo de destrucción cada 2 meses. Tu modelo es tuyo y puedes descargarlo cuando quieras.'
    },
    {
      question: '¿Por qué solo 12 dominios?',
      answer: 'Cada dominio tiene un modelo especializado, no uno genérico adaptado mal a todos. Preferimos hacer 12 dominios excelentes que 100 mediocres.'
    },
    {
      question: '¿Qué es "ajuste bimestral"?',
      answer: 'Cada 2 meses, tu modelo se ajusta con tus correcciones acumuladas. Sin guardar datos en cloud. El proceso de reentrenamiento es seguro y privado.'
    },
    {
      question: '¿Puedo cambiar de dominio después?',
      answer: 'No. El dominio es permanente por diseño arquitectónico. El modelo se especializa profundamente en tu contexto, por eso es importante elegir bien desde el inicio.'
    }
  ];

  const handleFAQExpand = (question) => {
    trackEvent(EVENTS.FAQ_EXPAND, { question });
  };

  return (
    <section 
      id="faq" 
      className="py-24 lg:py-32 cosmic-bg"
      data-testid="faq-section"
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
            Preguntas frecuentes
          </h2>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="max-w-3xl mx-auto"
        >
          <Accordion type="single" collapsible className="space-y-4">
            {faqs.map((faq, index) => (
              <AccordionItem 
                key={index} 
                value={`item-${index}`}
                className="bg-zinc-900/50 border border-zinc-800 rounded-xl px-6 data-[state=open]:border-[#FACC15]/30"
                data-testid={`faq-item-${index}`}
              >
                <AccordionTrigger 
                  onClick={() => handleFAQExpand(faq.question)}
                  className="text-left font-mono text-white hover:text-[#FACC15] hover:no-underline py-5"
                >
                  {faq.question}
                </AccordionTrigger>
                <AccordionContent className="text-zinc-400 pb-5">
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </motion.div>
      </div>
    </section>
  );
};
