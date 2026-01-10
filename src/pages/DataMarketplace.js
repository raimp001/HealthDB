import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

// Use relative URL in production (same origin), fallback to localhost in dev
const API_URL = process.env.NODE_ENV === 'production' ? '' : (process.env.REACT_APP_API_URL || 'http://localhost:8000');

const DataMarketplace = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_URL}/api/marketplace/products`)
      .then(res => res.json())
      .then(data => {
        const transformed = data.map(p => ({
          id: p.id,
          name: p.name,
          description: p.description,
          cancerTypes: p.cancer_types || [],
          category: p.category || 'Hematologic',
          patientCount: p.patient_count || 0,
          recordCount: p.record_count || 0,
          completeness: p.completeness_score || 0,
          dataCategories: p.data_categories || [],
          dateRange: p.date_range_start ? `${new Date(p.date_range_start).getFullYear()} - Present` : '2015 - Present',
          priceFrom: p.price_from || 0,
          isFeatured: p.is_featured,
          pricingTiers: p.pricing_tiers || { academic: p.price_from, startup: p.price_from * 2, enterprise: p.price_from * 4, pharma: p.price_from * 8 },
        }));
        setProducts(transformed);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to fetch products:', err);
        setLoading(false);
      });
  }, []);

  const categories = [
    { id: 'all', label: 'All' },
    { id: 'Hematologic', label: 'Hematologic' },
    { id: 'Solid Tumor', label: 'Solid Tumor' },
    { id: 'Cell Therapy', label: 'Cell Therapy' },
  ];

  const filteredProducts = products.filter((product) => {
    const matchesSearch = product.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         product.description.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || product.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
    }).format(price);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center pt-20">
        <div className="text-center">
          <div className="w-8 h-8 border border-white/20 border-t-white/60 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-white/40 text-sm">Loading research data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black pt-20">
      {/* Hero Section */}
      <section className="py-20 px-6 border-b border-white/5 relative overflow-hidden">
        <div className="absolute inset-0 gradient-bg opacity-50" />
        <div className="absolute top-1/2 right-0 w-[500px] h-[500px] bg-[#00d4aa]/5 rounded-full blur-[120px]" />
        
        <div className="max-w-6xl mx-auto relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-xs uppercase tracking-[0.3em] text-[#00d4aa] mb-4">
              Research Platform
            </p>
            <h1 className="heading-display text-4xl md:text-5xl lg:text-6xl text-white/90 mb-6">
              Accelerating Cancer Research
              <br />
              <span className="text-white/50">Through Ethical Data Sharing</span>
            </h1>
            <p className="text-white/50 text-lg max-w-3xl mb-8 leading-relaxed">
              We connect patient-contributed data with researchers conducting IRB-approved studies. 
              Every dataset is built on voluntary consent, rigorous de-identification, and 
              transparent governance—ensuring healthcare data is used ethically to advance 
              real-world evidence and improve patient outcomes.
            </p>
          </motion.div>

          {/* Mission Pillars */}
          <div className="grid md:grid-cols-4 gap-4 mt-12">
            {[
              {
                icon: '🤝',
                title: 'Consent-First',
                description: 'All data comes from patients who voluntarily chose to contribute',
              },
              {
                icon: '🔒',
                title: 'Privacy Protected',
                description: 'HIPAA-compliant de-identification protects patient identity',
              },
              {
                icon: '⚖️',
                title: 'Ethically Governed',
                description: 'IRB approval required for all research access',
              },
              {
                icon: '🔄',
                title: 'Feedback Loop',
                description: 'Insights shared back to improve patient care',
              },
            ].map((pillar, index) => (
              <motion.div
                key={pillar.title}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                className="p-5 border border-white/10 bg-white/5"
              >
                <span className="text-2xl mb-3 block">{pillar.icon}</span>
                <h3 className="text-white font-medium text-sm mb-1">{pillar.title}</h3>
                <p className="text-white/40 text-xs">{pillar.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section className="py-16 px-6 border-b border-white/5">
        <div className="max-w-6xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">
                Our Approach
              </p>
              <h2 className="heading-display text-2xl md:text-3xl text-white/90 mb-6">
                Building a trusted ecosystem for healthcare data
              </h2>
              <p className="text-white/40 leading-relaxed mb-6">
                Traditional healthcare data is siloed, inaccessible, and often used without 
                meaningful patient consent. We're changing that by putting patients in control 
                of their data and creating a transparent system where research benefits everyone.
              </p>
              <div className="space-y-4">
                {[
                  'Patients voluntarily contribute de-identified data',
                  'Researchers submit IRB-approved study protocols',
                  'Data access is logged and transparent to contributors',
                  'Findings are shared to accelerate future research',
                  'Patients receive compensation for their contributions',
                ].map((item, i) => (
                  <div key={i} className="flex items-start gap-3">
                    <span className="text-[#00d4aa] mt-1">✓</span>
                    <span className="text-white/60 text-sm">{item}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="card-glass p-6">
                <span className="text-3xl mb-3 block">🏥</span>
                <h3 className="text-white font-medium mb-2">For Institutions</h3>
                <p className="text-white/40 text-sm mb-4">Partner with us to contribute data and participate in multi-center studies</p>
                <a href="mailto:partnerships@healthdb.ai" className="text-[#00d4aa] text-sm hover:underline">
                  Become a partner →
                </a>
              </div>
              <div className="card-glass p-6">
                <span className="text-3xl mb-3 block">🔬</span>
                <h3 className="text-white font-medium mb-2">For Researchers</h3>
                <p className="text-white/40 text-sm mb-4">Access ethically-sourced data for your IRB-approved studies</p>
                <Link to="/researchers" className="text-[#00d4aa] text-sm hover:underline">
                  Learn more →
                </Link>
              </div>
              <div className="card-glass p-6">
                <span className="text-3xl mb-3 block">💊</span>
                <h3 className="text-white font-medium mb-2">For Industry</h3>
                <p className="text-white/40 text-sm mb-4">Real-world evidence to inform drug development and outcomes research</p>
                <a href="mailto:enterprise@healthdb.ai" className="text-[#00d4aa] text-sm hover:underline">
                  Contact us →
                </a>
              </div>
              <div className="card-glass p-6">
                <span className="text-3xl mb-3 block">👤</span>
                <h3 className="text-white font-medium mb-2">For Patients</h3>
                <p className="text-white/40 text-sm mb-4">Contribute your data to help advance research and earn rewards</p>
                <Link to="/patients" className="text-[#00d4aa] text-sm hover:underline">
                  Get started →
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Impact Section */}
      <section className="py-16 px-6 border-b border-white/5 bg-gradient-to-b from-transparent to-[#00d4aa]/5">
        <div className="max-w-6xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">
              Our Impact
            </p>
            <h2 className="heading-display text-2xl md:text-3xl text-white/90 mb-4">
              How your data makes a difference
            </h2>
            <p className="text-white/40 max-w-2xl mx-auto mb-12">
              Every data contribution helps researchers answer critical questions about cancer 
              treatment, accelerates drug development, and ultimately improves patient outcomes.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                icon: '📊',
                title: 'Real-World Evidence',
                description: 'Clinical trial data only tells part of the story. Real-world data reveals how treatments perform across diverse patient populations in actual clinical practice.',
              },
              {
                icon: '⚡',
                title: 'Faster Discovery',
                description: 'Aggregated data from thousands of patients helps researchers identify patterns and validate hypotheses faster than traditional methods.',
              },
              {
                icon: '🔄',
                title: 'Industry Feedback',
                description: 'Pharmaceutical and biotech companies use insights to improve drug development, identify unmet needs, and create better therapies.',
              },
            ].map((item, index) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="text-left p-6 border border-white/10"
              >
                <span className="text-3xl mb-4 block">{item.icon}</span>
                <h3 className="text-white font-medium mb-3">{item.title}</h3>
                <p className="text-white/40 text-sm leading-relaxed">{item.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Available Research Data */}
      <section className="py-16 px-6">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">
                Research Data
              </p>
              <h2 className="heading-display text-2xl md:text-3xl text-white/90">
                Available Datasets
              </h2>
              <p className="text-white/40 mt-2">
                All data is ethically sourced with patient consent
              </p>
            </div>
            <div className="flex gap-2">
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`px-4 py-2 text-xs uppercase tracking-wider transition-all ${
                    selectedCategory === cat.id
                      ? 'bg-white text-black'
                      : 'bg-transparent text-white/50 border border-white/10 hover:border-white/30'
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          {/* Search */}
          <div className="relative w-full md:w-96 mb-8">
            <input
              type="text"
              placeholder="Search by disease, treatment, or criteria..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-3 bg-white/5 border border-white/10 text-white placeholder-white/30 focus:border-white/30 focus:outline-none transition-colors"
            />
            <svg className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>

          {/* Products or Empty State */}
          {filteredProducts.filter(p => p.patientCount > 0).length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="text-center py-16 border border-white/10"
            >
              <div className="w-16 h-16 border border-white/10 rounded-full flex items-center justify-center mx-auto mb-8">
                <span className="text-3xl">🌱</span>
              </div>
              <h2 className="text-2xl font-light text-white mb-4">Building Our Data Network</h2>
              <p className="text-white/40 max-w-lg mx-auto mb-4">
                We're partnering with cancer centers and recruiting patient contributors to build 
                ethically-sourced, consent-based research datasets.
              </p>
              <p className="text-white/30 text-sm max-w-md mx-auto mb-8">
                Unlike traditional data brokers, every record in our system comes from a patient who 
                chose to contribute. This takes time, but ensures the highest ethical standards.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <Link 
                  to="/patients"
                  className="px-6 py-3 bg-white text-black text-xs uppercase tracking-wider font-medium hover:bg-gray-100 transition-colors"
                >
                  Contribute Your Data
                </Link>
                <a 
                  href="mailto:partnerships@healthdb.ai"
                  className="px-6 py-3 border border-white/20 text-white text-xs uppercase tracking-wider hover:bg-white/10 transition-colors"
                >
                  Partner With Us
                </a>
              </div>
            </motion.div>
          ) : (
            <div className="space-y-px">
              {filteredProducts.filter(p => p.patientCount > 0).map((product, index) => (
                <motion.div
                  key={product.id}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3, delay: index * 0.05 }}
                  onClick={() => setSelectedProduct(product)}
                  className="card-glass card-hover p-6 cursor-pointer group"
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex-grow">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-white font-medium group-hover:text-[#00d4aa] transition-colors">
                          {product.name}
                        </h3>
                        <span className="px-2 py-0.5 text-xs text-white/40 border border-white/10">
                          {product.category}
                        </span>
                        {product.isFeatured && (
                          <span className="px-2 py-0.5 text-xs text-[#00d4aa] border border-[#00d4aa]/30">
                            Featured
                          </span>
                        )}
                      </div>
                      <p className="text-white/40 text-sm">{product.description}</p>
                    </div>
                    <div className="flex items-center gap-8 text-sm">
                      <div>
                        <p className="text-white/30 text-xs">Contributors</p>
                        <p className="text-white font-mono">{product.patientCount.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-white/30 text-xs">Access Fee</p>
                        <p className="text-white font-mono">{formatPrice(product.priceFrom)}</p>
                      </div>
                      <button className="px-4 py-2 border border-white/20 text-white/60 text-xs uppercase tracking-wider hover:bg-white hover:text-black transition-all">
                        Details
                      </button>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Governance & Ethics */}
      <section className="py-16 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-12">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">
                Governance
              </p>
              <h2 className="heading-display text-2xl md:text-3xl text-white/90 mb-6">
                Our commitment to ethical data use
              </h2>
              <div className="space-y-6">
                {[
                  {
                    title: 'Patient Consent Required',
                    description: 'Every data record comes from a patient who explicitly consented to share their de-identified information for research purposes.',
                  },
                  {
                    title: 'IRB Approval Mandatory',
                    description: 'Researchers must have Institutional Review Board approval before accessing any patient-level data on our platform.',
                  },
                  {
                    title: 'Transparent Access Logs',
                    description: 'Patients can see exactly who accessed their data, for what purpose, and when. Full transparency builds trust.',
                  },
                  {
                    title: 'Revocable Consent',
                    description: 'Patients can withdraw their consent and request data deletion at any time. They remain in control.',
                  },
                ].map((item) => (
                  <div key={item.title} className="border-l-2 border-[#00d4aa]/30 pl-4">
                    <h3 className="text-white font-medium mb-1">{item.title}</h3>
                    <p className="text-white/40 text-sm">{item.description}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="card-glass p-8">
              <h3 className="text-white font-medium mb-6 text-lg">Data Use Guidelines</h3>
              <div className="space-y-4 mb-8">
                {[
                  { allowed: true, text: 'Academic and non-profit research' },
                  { allowed: true, text: 'Drug development and clinical trials' },
                  { allowed: true, text: 'Outcomes research and health economics' },
                  { allowed: true, text: 'AI/ML model training (with consent)' },
                  { allowed: false, text: 'Re-identification attempts' },
                  { allowed: false, text: 'Marketing or advertising' },
                  { allowed: false, text: 'Insurance underwriting' },
                  { allowed: false, text: 'Employment decisions' },
                ].map((item, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <span className={item.allowed ? 'text-[#00d4aa]' : 'text-red-400'}>
                      {item.allowed ? '✓' : '✕'}
                    </span>
                    <span className={`text-sm ${item.allowed ? 'text-white/60' : 'text-white/40'}`}>
                      {item.text}
                    </span>
                  </div>
                ))}
              </div>
              <div className="pt-6 border-t border-white/10">
                <p className="text-white/30 text-xs">
                  All data access is governed by our Data Use Agreement and monitored for compliance. 
                  Violations result in immediate termination of access.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 px-6 border-t border-white/5">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <h2 className="heading-display text-2xl md:text-3xl text-white/90 mb-4">
              Join the movement for ethical healthcare data
            </h2>
            <p className="text-white/40 mb-8 max-w-xl mx-auto">
              Whether you're a patient who wants to contribute, a researcher seeking data, 
              or an institution looking to partner—we'd love to hear from you.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Link to="/patients" className="px-6 py-3 bg-white text-black text-xs uppercase tracking-wider font-medium hover:bg-gray-100 transition-colors">
                I'm a Patient
              </Link>
              <Link to="/researchers" className="px-6 py-3 border border-white/20 text-white text-xs uppercase tracking-wider hover:bg-white/10 transition-colors">
                I'm a Researcher
              </Link>
              <a href="mailto:contact@healthdb.ai" className="px-6 py-3 border border-white/20 text-white text-xs uppercase tracking-wider hover:bg-white/10 transition-colors">
                I Represent an Institution
              </a>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Product Detail Modal */}
      {selectedProduct && (
        <div className="fixed inset-0 bg-black/90 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-black border border-white/10 max-w-3xl w-full max-h-[90vh] overflow-y-auto"
          >
            <div className="p-8 border-b border-white/10">
              <div className="flex justify-between items-start">
                <div>
                  <span className="text-xs text-white/40 uppercase tracking-wider">{selectedProduct.category}</span>
                  <h2 className="text-2xl font-medium text-white mt-2">{selectedProduct.name}</h2>
                </div>
                <button
                  onClick={() => setSelectedProduct(null)}
                  className="p-2 hover:bg-white/10 transition-colors"
                >
                  <svg className="w-5 h-5 text-white/60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <div className="p-8">
              <p className="text-white/50 mb-6">{selectedProduct.description}</p>
              
              <div className="p-4 bg-[#00d4aa]/10 border border-[#00d4aa]/20 mb-8">
                <p className="text-[#00d4aa] text-sm">
                  <strong>Ethically Sourced:</strong> This dataset is built entirely from voluntary patient contributions. 
                  All contributors have signed informed consent and can view access logs.
                </p>
              </div>

              <div className="grid grid-cols-4 gap-4 mb-8">
                {[
                  { label: 'Contributors', value: selectedProduct.patientCount.toLocaleString() },
                  { label: 'Records', value: selectedProduct.recordCount.toLocaleString() },
                  { label: 'Completeness', value: `${selectedProduct.completeness}%` },
                  { label: 'Date Range', value: selectedProduct.dateRange.split(' ')[0] },
                ].map((stat) => (
                  <div key={stat.label} className="p-4 bg-white/5 border border-white/5">
                    <p className="text-white/30 text-xs mb-1">{stat.label}</p>
                    <p className="text-white font-mono text-lg">{stat.value}</p>
                  </div>
                ))}
              </div>

              <div className="mb-8">
                <p className="text-xs uppercase tracking-[0.2em] text-white/40 mb-4">Access Tiers</p>
                <p className="text-white/30 text-sm mb-4">
                  Access fees support patient compensation, data infrastructure, and governance. Academic discounts available.
                </p>
                <div className="grid grid-cols-4 gap-4">
                  {Object.entries(selectedProduct.pricingTiers).map(([tier, price]) => (
                    <div key={tier} className="p-4 border border-white/10 text-center">
                      <p className="text-white/40 text-xs uppercase mb-2">{tier}</p>
                      <p className="text-white font-mono">{formatPrice(price)}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="flex gap-4">
                <Link to="/register?type=researcher" className="flex-1 py-3 bg-white text-black text-xs uppercase tracking-wider font-medium hover:bg-gray-100 transition-colors text-center">
                  Apply for Access
                </Link>
                <button className="flex-1 py-3 border border-white/20 text-white text-xs uppercase tracking-wider hover:bg-white/10 transition-colors">
                  Request Data Dictionary
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
};

export default DataMarketplace;
