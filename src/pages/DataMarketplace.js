import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

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
        // Transform API data to match component expectations
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
    { id: 'all', label: 'All Datasets' },
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
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading datasets...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-600 to-teal-600 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold mb-2">Data Marketplace</h1>
          <p className="text-emerald-100">Access curated, analysis-ready oncology datasets</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search and Filters */}
        <div className="bg-white rounded-xl shadow-sm p-4 mb-8 flex flex-col md:flex-row gap-4">
          <div className="flex-grow">
            <input
              type="text"
              placeholder="Search datasets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            />
          </div>
          <div className="flex gap-2">
            {categories.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setSelectedCategory(cat.id)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  selectedCategory === cat.id
                    ? 'bg-emerald-600 text-white'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>
        </div>

        {/* Featured Section */}
        <div className="mb-8">
          <h2 className="text-xl font-semibold text-slate-900 mb-4">Featured Datasets</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {filteredProducts.filter(p => p.isFeatured).map((product) => (
              <motion.div
                key={product.id}
                whileHover={{ y: -4 }}
                className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden cursor-pointer"
                onClick={() => setSelectedProduct(product)}
              >
                <div className="bg-gradient-to-r from-emerald-500 to-teal-500 p-4">
                  <span className="inline-flex items-center px-2 py-1 rounded-full bg-white/20 text-white text-xs font-medium">
                    ⭐ Featured
                  </span>
                </div>
                <div className="p-6">
                  <h3 className="font-semibold text-slate-900 mb-2">{product.name}</h3>
                  <p className="text-slate-600 text-sm mb-4 line-clamp-2">{product.description}</p>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {product.cancerTypes.slice(0, 2).map((type) => (
                      <span key={type} className="px-2 py-1 bg-slate-100 rounded text-xs text-slate-600">
                        {type}
                      </span>
                    ))}
                  </div>
                  <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                    <div>
                      <span className="text-slate-500">Patients</span>
                      <div className="font-semibold text-slate-900">{product.patientCount.toLocaleString()}</div>
                    </div>
                    <div>
                      <span className="text-slate-500">Completeness</span>
                      <div className="font-semibold text-slate-900">{product.completeness}%</div>
                    </div>
                  </div>
                  <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                    <div>
                      <span className="text-slate-500 text-sm">From</span>
                      <div className="font-bold text-emerald-600">{formatPrice(product.priceFrom)}</div>
                    </div>
                    <button className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700">
                      View Details
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>

        {/* All Products */}
        <div>
          <h2 className="text-xl font-semibold text-slate-900 mb-4">All Datasets</h2>
          <div className="space-y-4">
            {filteredProducts.map((product) => (
              <motion.div
                key={product.id}
                whileHover={{ scale: 1.01 }}
                className="bg-white rounded-xl shadow-sm border border-slate-100 p-6 cursor-pointer"
                onClick={() => setSelectedProduct(product)}
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="flex-grow">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-slate-900">{product.name}</h3>
                      <span className="px-2 py-1 bg-slate-100 rounded text-xs text-slate-600">
                        {product.category}
                      </span>
                    </div>
                    <p className="text-slate-600 text-sm mb-3">{product.description}</p>
                    <div className="flex flex-wrap gap-4 text-sm">
                      <span className="text-slate-500">
                        <strong className="text-slate-900">{product.patientCount.toLocaleString()}</strong> patients
                      </span>
                      <span className="text-slate-500">
                        <strong className="text-slate-900">{product.recordCount.toLocaleString()}</strong> records
                      </span>
                      <span className="text-slate-500">
                        <strong className="text-slate-900">{product.completeness}%</strong> completeness
                      </span>
                      <span className="text-slate-500">
                        <strong className="text-slate-900">{product.dateRange}</strong>
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <span className="text-slate-500 text-sm">From</span>
                      <div className="font-bold text-lg text-emerald-600">{formatPrice(product.priceFrom)}</div>
                    </div>
                    <button className="px-6 py-3 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700">
                      Learn More
                    </button>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </div>

      {/* Product Detail Modal */}
      {selectedProduct && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-2xl max-w-3xl w-full max-h-[90vh] overflow-y-auto"
          >
            <div className="bg-gradient-to-r from-emerald-500 to-teal-500 p-6 rounded-t-2xl">
              <div className="flex justify-between items-start">
                <div>
                  <span className="inline-flex items-center px-2 py-1 rounded-full bg-white/20 text-white text-xs font-medium mb-2">
                    {selectedProduct.category}
                  </span>
                  <h2 className="text-2xl font-bold text-white">{selectedProduct.name}</h2>
                </div>
                <button
                  onClick={() => setSelectedProduct(null)}
                  className="p-2 hover:bg-white/20 rounded-lg transition-colors"
                >
                  <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>

            <div className="p-6">
              <p className="text-slate-600 mb-6">{selectedProduct.description}</p>

              {/* Stats Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div className="bg-slate-50 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-slate-900">{selectedProduct.patientCount.toLocaleString()}</div>
                  <div className="text-sm text-slate-500">Patients</div>
                </div>
                <div className="bg-slate-50 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-slate-900">{selectedProduct.recordCount.toLocaleString()}</div>
                  <div className="text-sm text-slate-500">Records</div>
                </div>
                <div className="bg-slate-50 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-slate-900">{selectedProduct.completeness}%</div>
                  <div className="text-sm text-slate-500">Completeness</div>
                </div>
                <div className="bg-slate-50 rounded-lg p-4 text-center">
                  <div className="text-2xl font-bold text-slate-900">{selectedProduct.dateRange.split(' ')[0]}</div>
                  <div className="text-sm text-slate-500">Data From</div>
                </div>
              </div>

              {/* Data Categories */}
              <div className="mb-6">
                <h3 className="font-semibold text-slate-900 mb-3">Data Categories Included</h3>
                <div className="flex flex-wrap gap-2">
                  {selectedProduct.dataCategories.map((cat) => (
                    <span key={cat} className="px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-sm">
                      {cat}
                    </span>
                  ))}
                </div>
              </div>

              {/* Pricing Tiers */}
              <div className="mb-6">
                <h3 className="font-semibold text-slate-900 mb-3">Pricing Tiers</h3>
                <div className="grid md:grid-cols-4 gap-4">
                  {Object.entries(selectedProduct.pricingTiers).map(([tier, price]) => (
                    <div key={tier} className="border border-slate-200 rounded-lg p-4 text-center">
                      <div className="text-sm text-slate-500 capitalize mb-1">{tier}</div>
                      <div className="text-xl font-bold text-slate-900">{formatPrice(price)}</div>
                    </div>
                  ))}
                </div>
              </div>

              {/* CTA */}
              <div className="flex gap-4">
                <button className="flex-1 py-3 bg-emerald-600 text-white rounded-lg font-semibold hover:bg-emerald-700 transition-all">
                  Request Access
                </button>
                <button className="flex-1 py-3 border border-slate-300 text-slate-700 rounded-lg font-semibold hover:bg-slate-50 transition-all">
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

