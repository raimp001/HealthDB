import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';

const Navbar = () => {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 50);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    setMenuOpen(false);
  }, [location]);

  return (
    <nav
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'bg-black/80 backdrop-blur-xl border-b border-white/5'
          : 'bg-transparent'
      }`}
    >
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex items-center justify-between h-20">
          {/* Logo */}
          <Link to="/" className="flex items-center">
            <span className="text-white text-lg font-medium tracking-tight">
              HealthDB
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-1">
            <NavLink to="/marketplace">About</NavLink>
            <NavLink to="/researchers">Researchers</NavLink>
            <NavLink to="/patients">Patients</NavLink>
            <NavLink to="/resources">Resources</NavLink>
          </div>

          {/* Right Side */}
          <div className="hidden md:flex items-center space-x-4">
            <Link
              to="/login"
              className="text-white/60 hover:text-white text-sm transition-colors px-4 py-2"
            >
              Sign In
            </Link>
            <Link
              to="/register"
              className="px-5 py-2.5 bg-white text-black text-xs font-medium uppercase tracking-wider hover:bg-gray-100 transition-colors"
            >
              Get Started
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="md:hidden p-2 text-white"
            aria-label="Toggle menu"
          >
            <div className="w-6 h-5 flex flex-col justify-between">
              <span
                className={`block h-px bg-white transition-all duration-300 ${
                  menuOpen ? 'rotate-45 translate-y-2' : ''
                }`}
              />
              <span
                className={`block h-px bg-white transition-all duration-300 ${
                  menuOpen ? 'opacity-0' : ''
                }`}
              />
              <span
                className={`block h-px bg-white transition-all duration-300 ${
                  menuOpen ? '-rotate-45 -translate-y-2' : ''
                }`}
              />
            </div>
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      <div
        className={`md:hidden transition-all duration-300 overflow-hidden ${
          menuOpen ? 'max-h-screen bg-black/95 backdrop-blur-xl' : 'max-h-0'
        }`}
      >
        <div className="px-6 py-8 space-y-6">
          <MobileNavLink to="/marketplace">About</MobileNavLink>
          <MobileNavLink to="/researchers">Researchers</MobileNavLink>
          <MobileNavLink to="/patients">Patients</MobileNavLink>
          <MobileNavLink to="/resources">Resources</MobileNavLink>
          <div className="pt-6 border-t border-white/10 space-y-4">
            <Link
              to="/login"
              className="block text-white/60 hover:text-white transition-colors"
            >
              Sign In
            </Link>
            <Link
              to="/register"
              className="block px-5 py-3 bg-white text-black text-sm font-medium uppercase tracking-wider text-center"
            >
              Get Started
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
};

const NavLink = ({ to, children }) => {
  const location = useLocation();
  const isActive = location.pathname === to;

  return (
    <Link
      to={to}
      className={`px-4 py-2 text-sm transition-colors ${
        isActive
          ? 'text-white'
          : 'text-white/50 hover:text-white'
      }`}
    >
      {children}
    </Link>
  );
};

const MobileNavLink = ({ to, children }) => {
  const location = useLocation();
  const isActive = location.pathname === to;

  return (
    <Link
      to={to}
      className={`block text-2xl font-light ${
        isActive ? 'text-white' : 'text-white/50'
      }`}
    >
      {children}
    </Link>
  );
};

export default Navbar;
