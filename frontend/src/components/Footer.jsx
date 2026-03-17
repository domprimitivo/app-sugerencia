import { motion } from 'framer-motion';

export const Footer = () => {
  return (
    <footer 
      className="py-12 bg-[#09090B] border-t border-zinc-800"
      data-testid="footer"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col md:flex-row justify-between items-center gap-6">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <span className="font-mono text-xl font-bold text-[#FACC15]">
              MILEFORUM
            </span>
          </div>

          {/* Links */}
          <div className="flex items-center gap-8">
            <a 
              href="#producto" 
              className="text-zinc-500 hover:text-white transition-colors text-sm"
            >
              Producto
            </a>
            <a 
              href="#dominios" 
              className="text-zinc-500 hover:text-white transition-colors text-sm"
            >
              Dominios
            </a>
            <a 
              href="#precios" 
              className="text-zinc-500 hover:text-white transition-colors text-sm"
            >
              Precios
            </a>
            <a 
              href="#faq" 
              className="text-zinc-500 hover:text-white transition-colors text-sm"
            >
              FAQ
            </a>
          </div>

          {/* Copyright */}
          <div className="text-zinc-600 text-sm">
            © {new Date().getFullYear()} Mileforum. Tu operación, tu modelo.
          </div>
        </div>

        {/* Trust badge */}
        <motion.div
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true }}
          className="flex justify-center mt-8 pt-8 border-t border-zinc-800/50"
        >
          <div className="text-center">
            <p className="text-zinc-600 text-xs mb-2">
              Política Cero Datos · Recibo de destrucción certificado
            </p>
            <p className="text-zinc-700 text-xs">
              Hecho con propósito en México
            </p>
          </div>
        </motion.div>
      </div>
    </footer>
  );
};
