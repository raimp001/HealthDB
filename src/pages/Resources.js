import React from 'react';
import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';

const Resources = () => {
  const articles = [
    {
      id: 1,
      category: 'Research',
      title: 'The Future of Real-World Evidence in Oncology',
      excerpt: 'How patient-contributed data is transforming cancer research and accelerating treatment discoveries.',
      date: 'January 2026',
      readTime: '8 min read',
      slug: 'future-of-real-world-evidence'
    },
    {
      id: 2,
      category: 'Ethics',
      title: 'Building Trust Through Transparent Data Governance',
      excerpt: 'Why consent-first data sharing is essential for the future of healthcare research.',
      date: 'January 2026',
      readTime: '6 min read',
      slug: 'transparent-data-governance'
    },
    {
      id: 3,
      category: 'Technology',
      title: 'De-identification: Protecting Privacy While Enabling Research',
      excerpt: 'Technical approaches to ensuring patient privacy in longitudinal health data.',
      date: 'December 2025',
      readTime: '10 min read',
      slug: 'deidentification-privacy'
    },
    {
      id: 4,
      category: 'Industry',
      title: 'Multi-Center Collaboration: Breaking Down Data Silos',
      excerpt: 'How federated data networks enable large-scale oncology studies across institutions.',
      date: 'December 2025',
      readTime: '7 min read',
      slug: 'multi-center-collaboration'
    },
    {
      id: 5,
      category: 'Patients',
      title: 'Your Data, Your Choice: A Guide for Cancer Patients',
      excerpt: 'Understanding how your health data can contribute to research while maintaining control.',
      date: 'November 2025',
      readTime: '5 min read',
      slug: 'patient-data-guide'
    },
    {
      id: 6,
      category: 'Regulatory',
      title: 'Navigating IRB Approval for Data-Driven Studies',
      excerpt: 'Best practices for researchers seeking institutional review board approval.',
      date: 'November 2025',
      readTime: '9 min read',
      slug: 'irb-approval-guide'
    }
  ];

  const whitepapers = [
    {
      title: 'Ethical Framework for Health Data Sharing',
      description: 'Our comprehensive guide to consent-based data governance in oncology research.',
      pages: '24 pages'
    },
    {
      title: 'Technical Architecture for HIPAA-Compliant Data Platforms',
      description: 'How we built a secure, scalable infrastructure for sensitive health data.',
      pages: '18 pages'
    },
    {
      title: 'Real-World Evidence: From Data to Clinical Insights',
      description: 'Methodology for generating actionable insights from patient-contributed data.',
      pages: '32 pages'
    }
  ];

  const categoryColors = {
    'Research': 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    'Ethics': 'bg-blue-500/10 text-blue-400 border-blue-500/20',
    'Technology': 'bg-purple-500/10 text-purple-400 border-purple-500/20',
    'Industry': 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    'Patients': 'bg-rose-500/10 text-rose-400 border-rose-500/20',
    'Regulatory': 'bg-cyan-500/10 text-cyan-400 border-cyan-500/20'
  };

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Hero Section */}
      <section className="relative py-24 overflow-hidden">
        <div className="absolute inset-0 bg-[linear-gradient(rgba(16,185,129,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(16,185,129,0.03)_1px,transparent_1px)] bg-[size:60px_60px]" />
        
        <div className="max-w-6xl mx-auto px-6 relative">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <span className="inline-block px-3 py-1 text-xs font-medium tracking-wider text-emerald-400 border border-emerald-500/30 rounded-full mb-6">
              RESOURCES
            </span>
            
            <h1 className="text-4xl md:text-5xl font-bold mb-6 tracking-tight">
              Insights & Research
            </h1>
            
            <p className="text-xl text-neutral-400 max-w-2xl">
              Explore our thinking on ethical data sharing, real-world evidence, 
              and the future of oncology research.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Featured Articles */}
      <section className="py-16 border-t border-neutral-800">
        <div className="max-w-6xl mx-auto px-6">
          <h2 className="text-2xl font-bold mb-12">Latest Articles</h2>
          
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {articles.map((article, index) => (
              <motion.article
                key={article.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                className="group bg-neutral-900/50 border border-neutral-800 rounded-lg p-6 hover:border-neutral-700 transition-all duration-300"
              >
                <div className="flex items-center gap-3 mb-4">
                  <span className={`px-2 py-1 text-xs font-medium rounded border ${categoryColors[article.category]}`}>
                    {article.category}
                  </span>
                  <span className="text-xs text-neutral-500">{article.readTime}</span>
                </div>
                
                <h3 className="text-lg font-semibold mb-3 group-hover:text-emerald-400 transition-colors">
                  {article.title}
                </h3>
                
                <p className="text-sm text-neutral-400 mb-4 line-clamp-3">
                  {article.excerpt}
                </p>
                
                <div className="flex items-center justify-between">
                  <span className="text-xs text-neutral-500">{article.date}</span>
                  <span className="text-emerald-400 text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                    Read →
                  </span>
                </div>
              </motion.article>
            ))}
          </div>
        </div>
      </section>

      {/* Whitepapers */}
      <section className="py-16 border-t border-neutral-800 bg-neutral-900/30">
        <div className="max-w-6xl mx-auto px-6">
          <div className="flex items-center justify-between mb-12">
            <div>
              <h2 className="text-2xl font-bold mb-2">Whitepapers & Guides</h2>
              <p className="text-neutral-400">In-depth resources for researchers and institutions</p>
            </div>
          </div>
          
          <div className="grid md:grid-cols-3 gap-6">
            {whitepapers.map((paper, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.3 + index * 0.1 }}
                className="bg-black border border-neutral-800 rounded-lg p-6 hover:border-emerald-500/30 transition-all duration-300 group"
              >
                <div className="w-12 h-12 bg-emerald-500/10 rounded-lg flex items-center justify-center mb-4 group-hover:bg-emerald-500/20 transition-colors">
                  <svg className="w-6 h-6 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                </div>
                
                <h3 className="text-lg font-semibold mb-2">{paper.title}</h3>
                <p className="text-sm text-neutral-400 mb-4">{paper.description}</p>
                
                <div className="flex items-center justify-between">
                  <span className="text-xs text-neutral-500">{paper.pages}</span>
                  <button className="text-emerald-400 text-sm font-medium hover:text-emerald-300 transition-colors">
                    Download PDF →
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Newsletter CTA */}
      <section className="py-20 border-t border-neutral-800">
        <div className="max-w-3xl mx-auto px-6 text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <h2 className="text-3xl font-bold mb-4">Stay Updated</h2>
            <p className="text-neutral-400 mb-8">
              Get the latest insights on ethical data sharing and oncology research delivered to your inbox.
            </p>
            
            <form className="flex flex-col sm:flex-row gap-4 max-w-md mx-auto">
              <input
                type="email"
                placeholder="Enter your email"
                className="flex-1 px-4 py-3 bg-neutral-900 border border-neutral-700 rounded-lg text-white placeholder-neutral-500 focus:outline-none focus:border-emerald-500 transition-colors"
              />
              <button
                type="submit"
                className="px-6 py-3 bg-emerald-500 text-black font-semibold rounded-lg hover:bg-emerald-400 transition-colors"
              >
                Subscribe
              </button>
            </form>
            
            <p className="text-xs text-neutral-500 mt-4">
              No spam. Unsubscribe anytime.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Partners/Press Logos */}
      <section className="py-16 border-t border-neutral-800">
        <div className="max-w-6xl mx-auto px-6">
          <p className="text-center text-sm text-neutral-500 mb-8">
            Featured in
          </p>
          <div className="flex flex-wrap items-center justify-center gap-12 opacity-40">
            <span className="text-xl font-semibold tracking-tight">Nature Medicine</span>
            <span className="text-xl font-semibold tracking-tight">NEJM Catalyst</span>
            <span className="text-xl font-semibold tracking-tight">STAT News</span>
            <span className="text-xl font-semibold tracking-tight">Healthcare IT News</span>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Resources;
