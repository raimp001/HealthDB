import React, { useState, useEffect } from 'react';
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
          <p className="text-white/40 text-sm">Loading datasets...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black pt-20">
      {/* Header */}
      <section className="py-20 px-6 border-b border-white/5">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">
              Platform
            </p>
            <h1 className="heading-display text-4xl md:text-5xl lg:text-6xl text-white/90 mb-6">
              Data Marketplace
            </h1>
            <p className="text-white/40 text-lg max-w-2xl">
              Access curated, analysis-ready oncology datasets for research.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Search and Filters */}
      <section className="py-8 px-6 border-b border-white/5">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row gap-6 items-start md:items-center justify-between">
            <div className="relative w-full md:w-96">
              <input
                type="text"
                placeholder="Search datasets..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full px-4 py-3 bg-white/5 border border-white/10 text-white placeholder-white/30 focus:border-white/30 focus:outline-none transition-colors"
              />
              <svg className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
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
        </div>
      </section>

      {/* Products Grid */}
      <section className="py-12 px-6">
        <div className="max-w-6xl mx-auto">
          {filteredProducts.length === 0 ? (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="text-center py-20"
            >
              <div className="w-16 h-16 border border-white/10 rounded-full flex items-center justify-center mx-auto mb-8">
                <svg className="w-8 h-8 text-white/30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                </svg>
              </div>
              <h2 className="text-2xl font-light text-white mb-4">No Datasets Available Yet</h2>
              <p className="text-white/40 max-w-md mx-auto mb-8">
                We're building partnerships with leading cancer centers to bring you 
                high-quality, de-identified oncology datasets. Check back soon.
              </p>
              <div className="flex flex-col sm:flex-row gap-4 justify-center">
                <a 
                  href="/register?type=institution"
                  className="px-6 py-3 bg-white text-black text-xs uppercase tracking-wider font-medium hover:bg-gray-100 transition-colors"
                >
                  Partner With Us
                </a>
                <a 
                  href="/register?type=patient"
                  className="px-6 py-3 border border-white/20 text-white text-xs uppercase tracking-wider hover:bg-white/10 transition-colors"
                >
                  Contribute Your Data
                </a>
              </div>
            </motion.div>
          ) : (
            <>
              {/* Featured */}
              {filteredProducts.filter(p => p.isFeatured && p.patientCount > 0).length > 0 && (
                <div className="mb-16">
                  <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-8">Featured Datasets</p>
                  <div className="grid md:grid-cols-3 gap-px bg-white/5">
                    {filteredProducts.filter(p => p.isFeatured && p.patientCount > 0).map((product, index) => (
                      <motion.div
                        key={product.id}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.4, delay: index * 0.1 }}
                        onClick={() => setSelectedProduct(product)}
                        className="card-glass card-hover p-8 cursor-pointer group"
                      >
                        <div className="flex items-center gap-2 mb-4">
                          <span className="w-2 h-2 bg-[#00d4aa] rounded-full"></span>
                          <span className="text-xs text-[#00d4aa] uppercase tracking-wider">Featured</span>
                        </div>
                        <h3 className="text-lg font-medium text-white mb-3 group-hover:text-[#00d4aa] transition-colors">
                          {product.name}
                        </h3>
                        <p className="text-white/40 text-sm mb-6 line-clamp-2">{product.description}</p>
                        <div className="flex justify-between items-end">
                          <div>
                            <p className="text-white/30 text-xs mb-1">Patients</p>
                            <p className="text-white font-mono">{product.patientCount.toLocaleString()}</p>
                          </div>
                          <div className="text-right">
                            <p className="text-white/30 text-xs mb-1">From</p>
                            <p className="text-white font-mono">{formatPrice(product.priceFrom)}</p>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              )}

              {/* All Products - only show those with actual data */}
              {filteredProducts.filter(p => p.patientCount > 0).length > 0 ? (
                <div>
                  <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-8">All Datasets</p>
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
                            </div>
                            <p className="text-white/40 text-sm">{product.description}</p>
                          </div>
                          <div className="flex items-center gap-8 text-sm">
                            <div>
                              <p className="text-white/30 text-xs">Patients</p>
                              <p className="text-white font-mono">{product.patientCount.toLocaleString()}</p>
                            </div>
                            <div>
                              <p className="text-white/30 text-xs">From</p>
                              <p className="text-white font-mono">{formatPrice(product.priceFrom)}</p>
                            </div>
                            <button className="px-4 py-2 border border-white/20 text-white/60 text-xs uppercase tracking-wider hover:bg-white hover:text-black transition-all">
                              View
                            </button>
                          </div>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              ) : (
                <motion.div
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.6 }}
                  className="text-center py-20"
                >
                  <div className="w-16 h-16 border border-white/10 rounded-full flex items-center justify-center mx-auto mb-8">
                    <svg className="w-8 h-8 text-white/30" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                    </svg>
                  </div>
                  <h2 className="text-2xl font-light text-white mb-4">No Datasets Available Yet</h2>
                  <p className="text-white/40 max-w-md mx-auto mb-8">
                    We're building partnerships with leading cancer centers to bring you 
                    high-quality, de-identified oncology datasets. Check back soon.
                  </p>
                  <div className="flex flex-col sm:flex-row gap-4 justify-center">
                    <a 
                      href="/register?type=institution"
                      className="px-6 py-3 bg-white text-black text-xs uppercase tracking-wider font-medium hover:bg-gray-100 transition-colors"
                    >
                      Partner With Us
                    </a>
                    <a 
                      href="/register?type=patient"
                      className="px-6 py-3 border border-white/20 text-white text-xs uppercase tracking-wider hover:bg-white/10 transition-colors"
                    >
                      Contribute Your Data
                    </a>
                  </div>
                </motion.div>
              )}
            </>
          )}
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
              <p className="text-white/50 mb-8">{selectedProduct.description}</p>

              <div className="grid grid-cols-4 gap-4 mb-8">
                {[
                  { label: 'Patients', value: selectedProduct.patientCount.toLocaleString() },
                  { label: 'Records', value: selectedProduct.recordCount.toLocaleString() },
                  { label: 'Completeness', value: `${selectedProduct.completeness}%` },
                  { label: 'Range', value: selectedProduct.dateRange.split(' ')[0] },
                ].map((stat) => (
                  <div key={stat.label} className="p-4 bg-white/5 border border-white/5">
                    <p className="text-white/30 text-xs mb-1">{stat.label}</p>
                    <p className="text-white font-mono text-lg">{stat.value}</p>
                  </div>
                ))}
              </div>

              <div className="mb-8">
                <p className="text-xs uppercase tracking-[0.2em] text-white/40 mb-4">Pricing Tiers</p>
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
                <button className="flex-1 py-3 bg-white text-black text-xs uppercase tracking-wider font-medium hover:bg-gray-100 transition-colors">
                  Request Access
                </button>
                <button className="flex-1 py-3 border border-white/20 text-white text-xs uppercase tracking-wider hover:bg-white/10 transition-colors">
                  Download Sample
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
