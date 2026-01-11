import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

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
      .catch(() => setLoading(false));
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
    return matchesSearch && matchesCategory && product.patientCount > 0;
  });

  const formatPrice = (price) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 }).format(price);

  if (loading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center pt-20">
        <div className="w-6 h-6 border border-white/20 border-t-white/60 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black pt-20">
      {/* Hero */}
      <section className="py-16 px-6 border-b border-white/5">
        <div className="max-w-5xl mx-auto">
          <p className="text-sm text-emerald-400 uppercase tracking-wider mb-4">Platform</p>
          <h1 className="text-4xl font-bold mb-4">
            Ethical Cancer Research Data
          </h1>
          <p className="text-white/40 max-w-2xl mb-8">
            Patient-contributed, consent-based datasets for IRB-approved research.
          </p>
          <div className="grid md:grid-cols-4 gap-4">
            {[
              { title: 'Consent-Based', desc: 'Voluntary contributions' },
              { title: 'De-identified', desc: 'HIPAA compliant' },
              { title: 'IRB Required', desc: 'Ethical governance' },
              { title: 'Transparent', desc: 'Full access logs' },
            ].map((item) => (
              <div key={item.title} className="p-4 border border-white/10">
                <h3 className="font-medium text-sm mb-1">{item.title}</h3>
                <p className="text-xs text-white/40">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stakeholders */}
      <section className="py-12 px-6 border-b border-white/5">
        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-4 gap-4">
            <Link to="/patients" className="p-4 border border-white/10 hover:border-white/30 transition-colors">
              <h3 className="font-medium mb-1">Patients</h3>
              <p className="text-xs text-white/40">Contribute data, earn rewards</p>
            </Link>
            <Link to="/researchers" className="p-4 border border-white/10 hover:border-white/30 transition-colors">
              <h3 className="font-medium mb-1">Researchers</h3>
              <p className="text-xs text-white/40">Access for approved studies</p>
            </Link>
            <a href="mailto:enterprise@healthdb.ai" className="p-4 border border-white/10 hover:border-white/30 transition-colors">
              <h3 className="font-medium mb-1">Industry</h3>
              <p className="text-xs text-white/40">Real-world evidence</p>
            </a>
            <a href="mailto:partnerships@healthdb.ai" className="p-4 border border-white/10 hover:border-white/30 transition-colors">
              <h3 className="font-medium mb-1">Institutions</h3>
              <p className="text-xs text-white/40">Join the network</p>
            </a>
          </div>
        </div>
      </section>

      {/* Datasets */}
      <section className="py-12 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
            <div>
              <h2 className="text-2xl font-bold">Datasets</h2>
              <p className="text-sm text-white/40">All ethically sourced with consent</p>
            </div>
            <div className="flex gap-2">
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setSelectedCategory(cat.id)}
                  className={`px-3 py-1.5 text-xs uppercase tracking-wider transition-colors ${
                    selectedCategory === cat.id ? 'bg-white text-black' : 'border border-white/10 text-white/50 hover:border-white/30'
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>
          </div>

          <input
            type="text"
            placeholder="Search..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full md:w-64 px-3 py-2 bg-white/5 border border-white/10 text-white placeholder-white/30 focus:border-white/30 focus:outline-none mb-6"
          />

          {filteredProducts.length === 0 ? (
            <div className="text-center py-16 border border-white/10">
              <h2 className="text-xl font-medium mb-4">Building Our Network</h2>
              <p className="text-white/40 max-w-md mx-auto mb-6">
                We're partnering with cancer centers and recruiting patient contributors. 
                Every record comes from a patient who chose to contribute.
              </p>
              <div className="flex gap-4 justify-center">
                <Link to="/patients" className="px-6 py-2 bg-white text-black text-sm hover:bg-gray-100 transition-colors">
                  Contribute Data
                </Link>
                <a href="mailto:partnerships@healthdb.ai" className="px-6 py-2 border border-white/20 text-sm hover:bg-white/10 transition-colors">
                  Partner With Us
                </a>
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              {filteredProducts.map((product) => (
                <div
                  key={product.id}
                  onClick={() => setSelectedProduct(product)}
                  className="p-4 border border-white/10 hover:border-white/20 cursor-pointer transition-colors"
                >
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-3 mb-1">
                        <h3 className="font-medium">{product.name}</h3>
                        <span className="text-xs text-white/30">{product.category}</span>
                      </div>
                      <p className="text-sm text-white/40">{product.description}</p>
                    </div>
                    <div className="flex items-center gap-6 text-sm">
                      <div>
                        <p className="text-xs text-white/30">N</p>
                        <p className="font-mono">{product.patientCount.toLocaleString()}</p>
                      </div>
                      <div>
                        <p className="text-xs text-white/30">From</p>
                        <p className="font-mono">{formatPrice(product.priceFrom)}</p>
                      </div>
                      <button className="px-3 py-1.5 border border-white/20 text-xs hover:bg-white/10 transition-colors">
                        Details
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Governance */}
      <section className="py-12 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-8">
          <div>
            <h2 className="text-xl font-bold mb-6">Data Use</h2>
            <div className="space-y-3">
              {[
                { allowed: true, text: 'Academic research' },
                { allowed: true, text: 'Drug development' },
                { allowed: true, text: 'Outcomes research' },
                { allowed: true, text: 'AI/ML (with consent)' },
                { allowed: false, text: 'Re-identification' },
                { allowed: false, text: 'Marketing' },
                { allowed: false, text: 'Insurance underwriting' },
              ].map((item, i) => (
                <div key={i} className="flex items-center gap-2 text-sm">
                  <span className={item.allowed ? 'text-emerald-400' : 'text-red-400'}>{item.allowed ? '✓' : '×'}</span>
                  <span className={item.allowed ? 'text-white/60' : 'text-white/30'}>{item.text}</span>
                </div>
              ))}
            </div>
          </div>
          <div>
            <h2 className="text-xl font-bold mb-6">Governance</h2>
            <div className="space-y-4 text-sm text-white/40">
              <p>All data requires patient consent</p>
              <p>IRB approval mandatory for access</p>
              <p>Transparent access logs for contributors</p>
              <p>Revocable consent at any time</p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-12 px-6 border-t border-white/5">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl font-bold mb-4">Join ethical healthcare data</h2>
          <div className="flex gap-4 justify-center">
            <Link to="/patients" className="px-6 py-2 bg-white text-black text-sm hover:bg-gray-100 transition-colors">
              Patient
            </Link>
            <Link to="/researchers" className="px-6 py-2 border border-white/20 text-sm hover:bg-white/10 transition-colors">
              Researcher
            </Link>
            <a href="mailto:contact@healthdb.ai" className="px-6 py-2 border border-white/20 text-sm hover:bg-white/10 transition-colors">
              Institution
            </a>
          </div>
        </div>
      </section>

      {/* Modal */}
      {selectedProduct && (
        <div className="fixed inset-0 bg-black/90 z-50 flex items-center justify-center p-4">
          <div className="bg-black border border-white/10 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-white/10 flex justify-between items-start">
              <div>
                <span className="text-xs text-white/30">{selectedProduct.category}</span>
                <h2 className="text-xl font-medium mt-1">{selectedProduct.name}</h2>
              </div>
              <button onClick={() => setSelectedProduct(null)} className="text-white/40 hover:text-white">×</button>
            </div>
            <div className="p-6">
              <p className="text-white/40 mb-6">{selectedProduct.description}</p>
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/20 mb-6 text-sm text-emerald-400">
                Ethically sourced from voluntary patient contributions
              </div>
              <div className="grid grid-cols-4 gap-3 mb-6">
                <div className="p-3 bg-white/5">
                  <p className="text-xs text-white/30">N</p>
                  <p className="font-mono">{selectedProduct.patientCount.toLocaleString()}</p>
                </div>
                <div className="p-3 bg-white/5">
                  <p className="text-xs text-white/30">Records</p>
                  <p className="font-mono">{selectedProduct.recordCount.toLocaleString()}</p>
                </div>
                <div className="p-3 bg-white/5">
                  <p className="text-xs text-white/30">Complete</p>
                  <p className="font-mono">{selectedProduct.completeness}%</p>
                </div>
                <div className="p-3 bg-white/5">
                  <p className="text-xs text-white/30">Range</p>
                  <p className="font-mono">{selectedProduct.dateRange.split(' ')[0]}</p>
                </div>
              </div>
              <div className="flex gap-3">
                <Link to="/register?type=researcher" className="flex-1 py-2 bg-white text-black text-center text-sm hover:bg-gray-100 transition-colors">
                  Apply for Access
                </Link>
                <button className="flex-1 py-2 border border-white/20 text-sm hover:bg-white/10 transition-colors">
                  Data Dictionary
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataMarketplace;
