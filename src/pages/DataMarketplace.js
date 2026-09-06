import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const DataMarketplace = () => (
  <div className="min-h-screen bg-black text-white pt-24">
    <div className="max-w-4xl mx-auto px-6 py-20">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
        <span className="inline-block border border-amber-400/30 bg-amber-400/5 text-amber-300 px-3 py-1 text-xs uppercase tracking-wider mb-6">
          Not available
        </span>
        <h1 className="text-4xl md:text-5xl font-bold mb-6">Dataset marketplace is not open</h1>
        <p className="text-white/50 text-lg leading-relaxed max-w-3xl mb-10">
          HealthDB does not currently list, sell, license, or release patient datasets. This route is retained only so invited researchers can see the planned boundary without mistaking prototype records for products.
        </p>

        <div className="grid md:grid-cols-3 gap-4 mb-12">
          {[
            ['Production datasets', 'None available'],
            ['Pricing or purchases', 'Not enabled'],
            ['Export workflow', 'Not built'],
          ].map(([label, value]) => (
            <div key={label} className="border border-white/10 p-5">
              <p className="text-white/30 text-xs uppercase tracking-wider mb-2">{label}</p>
              <p className="text-white/80">{value}</p>
            </div>
          ))}
        </div>

        <div className="border border-white/10 p-7 mb-10">
          <h2 className="text-xl font-semibold mb-4">What can be evaluated now</h2>
          <ul className="space-y-3 text-white/50 text-sm">
            <li>• Cohort-feasibility interactions using controlled synthetic records</li>
            <li>• Variable-selection and study-workspace usability</li>
            <li>• Governance requirements for a future, independently reviewed release process</li>
          </ul>
        </div>

        <div className="flex flex-wrap gap-3">
          <Link to="/research" className="px-5 py-3 border border-white/20 text-sm hover:bg-white/5">Return to workspace</Link>
          <Link to="/contact?interest=researcher" className="px-5 py-3 bg-white text-black text-sm font-medium hover:bg-gray-100">Share research requirements</Link>
        </div>
      </motion.div>
    </div>
  </div>
);

export default DataMarketplace;
