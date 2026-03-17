import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Loader2, CheckCircle } from 'lucide-react';
import { 
  Scale, Ruler, Calculator, Briefcase, PenTool, Settings,
  Stethoscope, Bed, Utensils, ShoppingBag, Factory, Truck 
} from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './ui/select';
import { trackEvent, EVENTS } from '../lib/analytics';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const iconMap = {
  Scale, Ruler, Calculator, Briefcase, PenTool, Settings,
  Stethoscope, Bed, Utensils, ShoppingBag, Factory, Truck
};

const domains = [
  { id: 'abogado', name: 'Abogado', icon: 'Scale' },
  { id: 'arquitecto', name: 'Arquitecto', icon: 'Ruler' },
  { id: 'contador', name: 'Contador', icon: 'Calculator' },
  { id: 'consultor_pyme', name: 'Consultor PyME', icon: 'Briefcase' },
  { id: 'diseno_producto', name: 'Diseño Producto', icon: 'PenTool' },
  { id: 'operaciones', name: 'Operaciones', icon: 'Settings' },
  { id: 'clinica', name: 'Clínica', icon: 'Stethoscope' },
  { id: 'hotel', name: 'Hotel', icon: 'Bed' },
  { id: 'restaurante', name: 'Restaurante', icon: 'Utensils' },
  { id: 'retail', name: 'Retail', icon: 'ShoppingBag' },
  { id: 'fabrica', name: 'Fábrica', icon: 'Factory' },
  { id: 'logistica', name: 'Logística', icon: 'Truck' },
];

export const RegisterModal = ({ isOpen, onClose, preselectedDomain = null }) => {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    domain: preselectedDomain || ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    trackEvent(EVENTS.REGISTER_SUBMIT, { domain: formData.domain });

    try {
      const response = await fetch(`${API_URL}/api/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Error al registrar');
      }

      trackEvent(EVENTS.REGISTER_SUCCESS, { domain: formData.domain });
      setIsSuccess(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClose = () => {
    setFormData({ name: '', email: '', domain: preselectedDomain || '' });
    setIsSuccess(false);
    setError('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        data-testid="register-modal"
      >
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/80 backdrop-blur-sm"
          onClick={handleClose}
        />

        {/* Modal */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="relative w-full max-w-md bg-[#09090B] border border-zinc-800 rounded-2xl p-8 shadow-2xl"
        >
          {/* Close button */}
          <button
            onClick={handleClose}
            className="absolute top-4 right-4 p-2 text-zinc-500 hover:text-white transition-colors"
            data-testid="register-close-btn"
          >
            <X className="w-5 h-5" />
          </button>

          {isSuccess ? (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="text-center py-8"
            >
              <div className="w-16 h-16 bg-[#FACC15]/10 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle className="w-8 h-8 text-[#FACC15]" />
              </div>
              <h3 className="font-mono text-2xl font-bold text-white mb-4">
                ¡Registro exitoso!
              </h3>
              <p className="text-zinc-400 mb-6">
                Pronto recibirás instrucciones para comenzar con tu Aprendiz.
              </p>
              <Button
                onClick={handleClose}
                className="bg-[#FACC15] text-black hover:bg-[#FDE047]"
                data-testid="register-success-close-btn"
              >
                Cerrar
              </Button>
            </motion.div>
          ) : (
            <>
              <div className="mb-8">
                <h3 className="font-mono text-2xl font-bold text-white mb-2">
                  Registrarse
                </h3>
                <p className="text-zinc-400">
                  Selecciona tu dominio para comenzar
                </p>
              </div>

              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="name" className="text-zinc-300">
                    Nombre completo
                  </Label>
                  <Input
                    id="name"
                    type="text"
                    placeholder="Tu nombre"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                    className="bg-zinc-900 border-zinc-800 text-white placeholder:text-zinc-600 focus:border-[#FACC15] focus:ring-[#FACC15]"
                    data-testid="register-name-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email" className="text-zinc-300">
                    Email
                  </Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="tu@email.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    required
                    className="bg-zinc-900 border-zinc-800 text-white placeholder:text-zinc-600 focus:border-[#FACC15] focus:ring-[#FACC15]"
                    data-testid="register-email-input"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="domain" className="text-zinc-300">
                    Dominio profesional
                  </Label>
                  <Select
                    value={formData.domain}
                    onValueChange={(value) => setFormData({ ...formData, domain: value })}
                    required
                  >
                    <SelectTrigger 
                      className="bg-zinc-900 border-zinc-800 text-white focus:border-[#FACC15] focus:ring-[#FACC15]"
                      data-testid="register-domain-select"
                    >
                      <SelectValue placeholder="Selecciona tu dominio" />
                    </SelectTrigger>
                    <SelectContent className="bg-zinc-900 border-zinc-800">
                      {domains.map((domain) => {
                        const IconComponent = iconMap[domain.icon];
                        return (
                          <SelectItem 
                            key={domain.id} 
                            value={domain.id}
                            className="text-white hover:bg-zinc-800 focus:bg-zinc-800"
                            data-testid={`domain-option-${domain.id}`}
                          >
                            <div className="flex items-center gap-2">
                              <IconComponent className="w-4 h-4 text-zinc-400" />
                              <span>{domain.name}</span>
                            </div>
                          </SelectItem>
                        );
                      })}
                    </SelectContent>
                  </Select>
                  <p className="text-xs text-zinc-500">
                    Importante: El dominio es permanente, elige con cuidado
                  </p>
                </div>

                {error && (
                  <motion.p
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    className="text-red-400 text-sm"
                    data-testid="register-error"
                  >
                    {error}
                  </motion.p>
                )}

                <Button
                  type="submit"
                  disabled={isLoading || !formData.domain}
                  className="w-full bg-[#FACC15] text-black hover:bg-[#FDE047] font-semibold py-6 disabled:opacity-50"
                  data-testid="register-submit-btn"
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Registrando...
                    </>
                  ) : (
                    'Comenzar ahora'
                  )}
                </Button>
              </form>
            </>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};
