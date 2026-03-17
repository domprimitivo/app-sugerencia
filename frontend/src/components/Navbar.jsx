import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X } from 'lucide-react';
import { Button } from './ui/button';
import { Sheet, SheetContent, SheetTrigger } from './ui/sheet';
import { trackEvent, EVENTS } from '../lib/analytics';

export const Navbar = ({ onRegisterClick }) => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 50);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navItems = [
    { label: 'Producto', href: '#solucion' },
    { label: 'Dominios', href: '#dominios' },
    { label: 'Precios', href: '#precios' },
  ];

  const handleNavClick = (item) => {
    trackEvent(EVENTS.NAV_CLICK, { section: item.label });
    setIsMobileMenuOpen(false);
  };

  return (
    <motion.nav
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5 }}
      className={`fixed top-0 left-0 right-0 z-50 transition-colors duration-300 ${
        isScrolled ? 'glass border-b border-zinc-800' : 'bg-transparent'
      }`}
      data-testid="navbar"
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 lg:h-20">
          {/* Logo */}
          <a href="#" className="flex items-center gap-2" data-testid="navbar-logo">
            <span className="font-mono text-xl lg:text-2xl font-bold text-[#FACC15]">
              MILEFORUM
            </span>
          </a>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            {navItems.map((item) => (
              <a
                key={item.label}
                href={item.href}
                onClick={() => handleNavClick(item)}
                className="text-zinc-400 hover:text-white transition-colors duration-200 font-medium"
                data-testid={`nav-${item.label.toLowerCase()}`}
              >
                {item.label}
              </a>
            ))}
          </div>

          {/* Desktop CTA Buttons */}
          <div className="hidden md:flex items-center gap-4">
            <Button
              variant="ghost"
              className="text-zinc-400 hover:text-white hover:bg-transparent"
              onClick={() => {
                trackEvent(EVENTS.NAV_CLICK, { section: 'Entrar' });
              }}
              data-testid="nav-login-btn"
            >
              Entrar
            </Button>
            <Button
              onClick={onRegisterClick}
              className="bg-[#FACC15] text-black hover:bg-[#FDE047] font-semibold px-6"
              data-testid="nav-register-btn"
            >
              Registrarse
            </Button>
          </div>

          {/* Mobile Menu */}
          <Sheet open={isMobileMenuOpen} onOpenChange={setIsMobileMenuOpen}>
            <SheetTrigger asChild className="md:hidden">
              <Button variant="ghost" size="icon" data-testid="mobile-menu-btn">
                <Menu className="h-6 w-6 text-white" />
              </Button>
            </SheetTrigger>
            <SheetContent side="right" className="bg-[#09090B] border-zinc-800 w-[300px]">
              <div className="flex flex-col gap-6 mt-8">
                {navItems.map((item) => (
                  <a
                    key={item.label}
                    href={item.href}
                    onClick={() => handleNavClick(item)}
                    className="text-lg text-zinc-400 hover:text-white transition-colors"
                    data-testid={`mobile-nav-${item.label.toLowerCase()}`}
                  >
                    {item.label}
                  </a>
                ))}
                <div className="border-t border-zinc-800 pt-6 flex flex-col gap-4">
                  <Button
                    variant="outline"
                    className="w-full border-zinc-700 text-white hover:bg-zinc-800"
                    data-testid="mobile-login-btn"
                  >
                    Entrar
                  </Button>
                  <Button
                    onClick={() => {
                      setIsMobileMenuOpen(false);
                      onRegisterClick();
                    }}
                    className="w-full bg-[#FACC15] text-black hover:bg-[#FDE047] font-semibold"
                    data-testid="mobile-register-btn"
                  >
                    Registrarse
                  </Button>
                </div>
              </div>
            </SheetContent>
          </Sheet>
        </div>
      </div>
    </motion.nav>
  );
};
