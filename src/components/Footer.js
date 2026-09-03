import React from 'react';
import { Link, useLocation } from 'react-router-dom';

const footerSections = [
  {
    title: 'Solutions',
    links: [
      { to: '/researchers', label: 'For Researchers' },
      { to: '/patients', label: 'For Patients' },
      { to: '/institutions', label: 'For Institutions' },
      { to: '/pricing', label: 'Pricing' },
    ],
  },
  {
    title: 'Roadmap',
    links: [
      { to: '/status', label: 'Platform status' },
      { to: '/platform', label: 'Roadmap' },
      { to: '/security-posture', label: 'Target Security' },
      { to: '/data-flow', label: 'Target Data Flow' },
      { to: '/repo-analyzer', label: 'Module Map' },
    ],
  },
  {
    title: 'Product',
    links: [
      { to: '/marketplace', label: 'Data Marketplace' },
      { to: '/cohort-builder', label: 'Cohort Builder' },
      { to: '/resources', label: 'Resources' },
    ],
  },
  {
    title: 'Company',
    links: [
      { to: '/about', label: 'About' },
      { to: '/contact', label: 'Contact' },
      { to: '/privacy', label: 'Privacy' },
      { to: '/terms', label: 'Terms' },
    ],
  },
];

const Footer = () => {
  const location = useLocation();

  // Auth screens are full-bleed centered layouts; a footer breaks their composition.
  if (['/login', '/register', '/reset-password', '/verify-email'].includes(location.pathname)) {
    return null;
  }

  return (
    <footer className="border-t border-white/5 py-12 px-6 bg-black">
      <div className="max-w-5xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
          <div className="col-span-2 md:col-span-1">
            <div className="font-medium mb-4 text-white">HealthDB</div>
            <p className="text-white/50 text-sm">Cancer research data infrastructure</p>
          </div>

          {footerSections.map((section) => (
            <div key={section.title}>
              <p className="text-xs text-white/50 uppercase tracking-wider mb-4">{section.title}</p>
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

        <div className="pt-8 border-t border-white/5 flex flex-col sm:flex-row justify-between gap-2 text-xs text-white/50">
          <p>© {new Date().getFullYear()} HealthDB</p>
          <p>Closed pilot · Not for clinical use</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
