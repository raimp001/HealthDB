import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const ForPatients = () => (
  <div className="bg-black text-white min-h-screen">
    <section className="py-28 px-6">
      <div className="max-w-5xl mx-auto">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55 }}
          className="max-w-3xl"
        >
          <p className="text-xs text-emerald-300 uppercase tracking-[0.2em] mb-5">For patients and caregivers · design stage</p>
          <h1 className="text-4xl md:text-6xl font-medium mb-7">Research data sharing should be understandable and controllable.</h1>
          <p className="text-lg text-white/50 max-w-2xl mb-9 leading-relaxed">
            HealthDB is testing how consent, privacy choices, and access history could work in one place.
            We are not enrolling patients or accepting medical records.
          </p>
          <div className="flex flex-col sm:flex-row gap-3">
            <Link to="/contact?interest=patient" className="px-7 py-3.5 bg-white text-black text-center font-medium hover:bg-gray-100 transition-colors">
              Join patient-design conversations
            </Link>
            <a href="#principles" className="px-7 py-3.5 border border-white/20 text-center hover:bg-white/5 transition-colors">
              See the design principles
            </a>
          </div>
        </motion.div>
      </div>
    </section>

    <section id="principles" className="py-20 px-6 border-t border-white/5 scroll-mt-32">
      <div className="max-w-5xl mx-auto">
        <p className="text-xs uppercase tracking-[0.2em] text-white/35 mb-3">Design principles</p>
        <h2 className="text-3xl font-medium mb-10">The product should earn trust through behavior</h2>
        <div className="grid md:grid-cols-2 gap-5">
          {[
            ['Plain-language choices', 'Explain what data is requested, why it is needed, who may use it, and what the limits are.'],
            ['Specific permission', 'Separate research purposes instead of hiding them inside one broad consent.'],
            ['Visible history', 'Show access events and study context in language a contributor can understand.'],
            ['Real withdrawal controls', 'Make future-use withdrawal clear, immediate, and honest about data already released.'],
          ].map(([title, description]) => (
            <article key={title} className="p-6 border border-white/10">
              <h3 className="font-medium text-lg mb-3">{title}</h3>
              <p className="text-sm text-white/45 leading-relaxed">{description}</p>
            </article>
          ))}
        </div>
      </div>
    </section>

    <section className="py-20 px-6 border-t border-white/5">
      <div className="max-w-5xl mx-auto grid md:grid-cols-[1.1fr_0.9fr] gap-12">
        <div>
          <p className="text-xs uppercase tracking-[0.2em] text-blue-300 mb-3">What we want to learn</p>
          <h2 className="text-3xl font-medium mb-6">Patient feedback that changes the product</h2>
          <ul className="space-y-4 text-sm text-white/50">
            <li>Which explanations feel clear—and which sound like legal camouflage?</li>
            <li>What controls must remain available after data is contributed?</li>
            <li>Which access details would be useful instead of overwhelming?</li>
            <li>What would make you stop and ask a human before continuing?</li>
          </ul>
        </div>
        <aside className="p-6 border border-amber-400/20">
          <p className="text-xs uppercase tracking-[0.2em] text-amber-300 mb-4">Please do not submit</p>
          <ul className="space-y-4 text-sm text-white/50">
            <li>Medical records or portal exports</li>
            <li>Names, dates of birth, record numbers, or other identifiers</li>
            <li>Questions requiring medical advice or urgent care</li>
          </ul>
          <p className="text-xs text-white/30 mt-6">HealthDB is a software prototype, not a healthcare provider or clinical service.</p>
        </aside>
      </div>
    </section>

    <section className="py-20 px-6 border-t border-white/5 text-center">
      <div className="max-w-3xl mx-auto">
        <h2 className="text-3xl font-medium mb-4">Help us make the workflow worthy of real-world testing</h2>
        <p className="text-white/45 mb-8">Share your perspective without sharing health information.</p>
        <Link to="/contact?interest=patient" className="inline-block px-8 py-3.5 bg-white text-black font-medium hover:bg-gray-100 transition-colors">
          Contact the product team
        </Link>
      </div>
    </section>
  </div>
);

export default ForPatients;
