import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const Pricing = () => (
  <div className="min-h-screen bg-black text-white">
    <section className="py-28 px-6">
      <div className="max-w-4xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55 }}
          className="max-w-3xl"
        >
          <p className="text-xs text-emerald-300 uppercase tracking-[0.2em] mb-5">Pilot access</p>
          <h1 className="text-4xl md:text-6xl font-medium mb-7">There is no public pricing yet.</h1>
          <p className="text-lg text-white/50 max-w-2xl leading-relaxed">
            HealthDB is validating the product with invited evaluators using synthetic data. We are
            not selling datasets, subscriptions, exports, or institutional integrations.
          </p>
        </motion.div>
      </div>
    </section>

    <section className="py-20 px-6 border-t border-white/5">
      <div className="max-w-4xl mx-auto grid md:grid-cols-2 gap-5">
        <article className="p-7 border border-emerald-400/20">
          <p className="text-xs uppercase tracking-[0.2em] text-emerald-300 mb-4">Current access</p>
          <h2 className="text-2xl font-medium mb-4">Guided pilot evaluation</h2>
          <p className="text-sm text-white/45 leading-relaxed mb-7">
            A focused walkthrough of one workflow with synthetic data, followed by structured product,
            safety, and governance feedback.
          </p>
          <Link to="/contact" className="inline-block px-6 py-3 bg-white text-black text-sm font-medium hover:bg-gray-100 transition-colors">
            Request a conversation
          </Link>
        </article>
        <article className="p-7 border border-white/10">
          <p className="text-xs uppercase tracking-[0.2em] text-white/35 mb-4">Future commercial model</p>
          <h2 className="text-2xl font-medium mb-4">To be validated</h2>
          <p className="text-sm text-white/45 leading-relaxed">
            Pricing, service levels, academic access, and data-partnership terms will be defined only
            after the workflows, controls, operating costs, and legal model have been validated.
          </p>
        </article>
      </div>
    </section>

    <section className="py-20 px-6 border-t border-white/5 text-center">
      <div className="max-w-2xl mx-auto">
        <h2 className="text-3xl font-medium mb-4">Interested in shaping the pilot?</h2>
        <p className="text-white/45 mb-8">Tell us which research or governance workflow you want to evaluate.</p>
        <Link to="/contact" className="text-emerald-300 hover:underline">Contact HealthDB →</Link>
      </div>
    </section>
  </div>
);

export default Pricing;
