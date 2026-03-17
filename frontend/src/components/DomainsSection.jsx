import { motion } from 'framer-motion';
import { 
  Scale, Ruler, Calculator, Briefcase, PenTool, Settings,
  Stethoscope, Bed, Utensils, ShoppingBag, Factory, Truck 
} from 'lucide-react';
import { trackEvent, EVENTS } from '../lib/analytics';

const iconMap = {
  Scale, Ruler, Calculator, Briefcase, PenTool, Settings,
  Stethoscope, Bed, Utensils, ShoppingBag, Factory, Truck
};

export const DomainsSection = ({ onDomainSelect }) => {
  const professionalDomains = [
    { id: 'abogado', name: 'Abogado', icon: 'Scale' },
    { id: 'arquitecto', name: 'Arquitecto', icon: 'Ruler' },
    { id: 'contador', name: 'Contador', icon: 'Calculator' },
    { id: 'consultor_pyme', name: 'Consultor PyME', icon: 'Briefcase' },
    { id: 'diseno_producto', name: 'Diseño Producto', icon: 'PenTool' },
    { id: 'operaciones', name: 'Operaciones', icon: 'Settings' },
  ];

  const businessDomains = [
    { id: 'clinica', name: 'Clínica', icon: 'Stethoscope' },
    { id: 'hotel', name: 'Hotel', icon: 'Bed' },
    { id: 'restaurante', name: 'Restaurante', icon: 'Utensils' },
    { id: 'retail', name: 'Retail', icon: 'ShoppingBag' },
    { id: 'fabrica', name: 'Fábrica', icon: 'Factory' },
    { id: 'logistica', name: 'Logística', icon: 'Truck' },
  ];

  const handleDomainHover = (domain) => {
    trackEvent(EVENTS.DOMAIN_HOVER, { domain: domain.id });
  };

  const handleDomainClick = (domain) => {
    trackEvent(EVENTS.DOMAIN_SELECT, { domain: domain.id });
    if (onDomainSelect) {
      onDomainSelect(domain.id);
    }
  };

  const DomainCard = ({ domain, index }) => {
    const IconComponent = iconMap[domain.icon];
    
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        whileInView={{ opacity: 1, scale: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.4, delay: index * 0.05 }}
        whileHover={{ y: -4 }}
        onMouseEnter={() => handleDomainHover(domain)}
        onClick={() => handleDomainClick(domain)}
        className="domain-card rounded-xl p-5 cursor-pointer group"
        data-testid={`domain-card-${domain.id}`}
      >
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-lg bg-zinc-800 flex items-center justify-center group-hover:bg-[#FACC15]/10 transition-colors duration-300">
            <IconComponent className="w-6 h-6 text-zinc-400 group-hover:text-[#FACC15] transition-colors duration-300" />
          </div>
          <span className="font-medium text-zinc-300 group-hover:text-white transition-colors duration-300">
            {domain.name}
          </span>
        </div>
      </motion.div>
    );
  };

  return (
    <section 
      id="dominios" 
      className="py-24 lg:py-32 bg-[#09090B]"
      data-testid="domains-section"
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
            12 dominios especializados
          </h2>
          <p className="text-zinc-400 text-lg max-w-2xl mx-auto">
            Cada dominio tiene su propio Aprendiz, entrenado para entender tu contexto profesional específico
          </p>
        </motion.div>

        {/* Professional domains */}
        <div className="mb-12">
          <motion.h3
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="font-mono text-sm text-[#FACC15] uppercase tracking-wider mb-6"
          >
            Para profesionales unipersonales
          </motion.h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {professionalDomains.map((domain, index) => (
              <DomainCard key={domain.id} domain={domain} index={index} />
            ))}
          </div>
        </div>

        {/* Business domains */}
        <div>
          <motion.h3
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            className="font-mono text-sm text-[#3B82F6] uppercase tracking-wider mb-6"
          >
            Para empresas
          </motion.h3>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            {businessDomains.map((domain, index) => (
              <DomainCard key={domain.id} domain={domain} index={index + 6} />
            ))}
          </div>
        </div>

        <motion.p
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          transition={{ delay: 0.5 }}
          className="text-center text-zinc-500 mt-12 text-sm"
        >
          Cada dominio con su propio Aprendiz especializado
        </motion.p>
      </div>
    </section>
  );
};
