import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const footerSections = [
  {
    title: 'Explore',
    links: [
      { to: '/researchers', label: 'For Researchers' },
      { to: '/patients', label: 'For Patients' },
      { to: '/institutions', label: 'For Institutions' },
    ],
  },
  {
    title: 'Roadmap',
    links: [
      { to: '/platform', label: 'Roadmap' },
      { to: '/security-posture', label: 'Security Status' },
      { to: '/data-flow', label: 'Current Data Flow' },
    ],
  },
  {
    title: 'Company',
    links: [
      { to: '/about', label: 'About' },
      { to: '/resources', label: 'Resources' },
      { to: '/contact', label: 'Contact' },
      { to: '/privacy', label: 'Privacy' },
      { to: '/terms', label: 'Terms' },
    ],
  },
];

const Footer = () => {
  const location = useLocation();

  // Auth screens are full-bleed centered layouts; a footer breaks their composition.
  if (location.pathname === '/login' || location.pathname === '/register') {
    return null;
  }

  return (
    <footer className="border-t border-white/5 py-12 px-6 bg-black">
      <div className="max-w-5xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-12">
          <div className="col-span-2 md:col-span-1">
            <div className="font-medium mb-4 text-white">HealthDB</div>
            <p className="text-white/30 text-sm">Oncology research workflow pilot</p>
          </div>

          {footerSections.map((section) => (
            <div key={section.title}>
              <p className="text-xs text-white/30 uppercase tracking-wider mb-4">{section.title}</p>
              <ul className="space-y-2 text-sm">
                {section.links.map((link) => (
                  <li key={link.to}>
                    <Link to={link.to} className="text-white/50 hover:text-white transition-colors">
                      {link.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="pt-8 border-t border-white/5 flex flex-col sm:flex-row justify-between gap-2 text-xs text-white/30">
          <p>© {new Date().getFullYear()} HealthDB</p>
          <p>Synthetic-data pilot · Not for clinical use</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
