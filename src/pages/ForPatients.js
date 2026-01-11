import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const ForPatients = () => {
  return (
    <div className="bg-black text-white min-h-screen">
      {/* Hero */}
      <section className="py-32 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <p className="text-sm text-emerald-400 uppercase tracking-wider mb-4">For Patients</p>
            <h1 className="text-4xl md:text-5xl font-bold mb-6">
              Your data advances research
            </h1>
            <p className="text-lg text-white/40 max-w-2xl mb-8">
              Contribute de-identified health data to help researchers discover treatments. 
              You control what you share. Earn rewards for contributions.
            </p>
            <div className="flex gap-4">
              <Link to="/register?type=patient" className="px-8 py-3 bg-white text-black font-medium hover:bg-gray-100 transition-colors">
                Join Now
              </Link>
              <a href="#how" className="px-8 py-3 border border-white/20 hover:bg-white/5 transition-colors">
                Learn More
              </a>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Why */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold mb-12">Why contribute?</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { title: 'Advance Research', desc: 'Your journey data helps researchers understand cancer and develop better treatments.' },
              { title: 'Help Future Patients', desc: 'Insights from your data may help doctors make better treatment decisions.' },
              { title: 'Earn Rewards', desc: 'Receive points for contributions, redeemable for gift cards or donations.' },
            ].map((item) => (
              <div key={item.title} className="p-6 border border-white/10">
                <h3 className="font-medium mb-3">{item.title}</h3>
                <p className="text-sm text-white/40">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how" className="py-20 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-16">
          <div>
            <h2 className="text-2xl font-bold mb-6">How it works</h2>
            <p className="text-white/40 mb-8">
              Contributing is voluntary. You control what you share and can revoke access anytime.
            </p>
            <Link to="/register?type=patient" className="px-6 py-3 bg-white text-black font-medium hover:bg-gray-100 transition-colors inline-block">
              Get Started
            </Link>
          </div>
          <div className="space-y-6">
            {[
              { step: '1', title: 'Create Account', desc: 'Sign up for free' },
              { step: '2', title: 'Review Consent', desc: 'Clear explanation of data use' },
              { step: '3', title: 'Connect Records', desc: 'MyChart, Cerner, or upload' },
              { step: '4', title: 'Data De-identified', desc: 'Name, SSN, dates never shared' },
              { step: '5', title: 'Earn Rewards', desc: 'Points when researchers access data' },
            ].map((item) => (
              <div key={item.step} className="flex gap-4">
                <span className="text-white/20 text-lg">{item.step}</span>
                <div>
                  <div className="font-medium">{item.title}</div>
                  <div className="text-sm text-white/40">{item.desc}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Privacy */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl font-bold mb-8">Your privacy</h2>
          <div className="grid md:grid-cols-4 gap-6 mb-12">
            {[
              { title: 'HIPAA Compliant', desc: 'Strict privacy regulations' },
              { title: 'De-identified', desc: 'Identity protected' },
              { title: 'Your Control', desc: 'Revoke anytime' },
              { title: 'Transparent', desc: 'See who accessed' },
            ].map((item) => (
              <div key={item.title} className="text-center p-4">
                <h3 className="font-medium mb-2">{item.title}</h3>
                <p className="text-sm text-white/40">{item.desc}</p>
              </div>
            ))}
          </div>
          <div className="p-6 border border-white/10">
            <h3 className="font-medium mb-4">Never shared</h3>
            <div className="grid sm:grid-cols-2 gap-2 text-sm text-white/50">
              {['Full name', 'SSN', 'Exact birth date', 'Address', 'Phone', 'Email', 'Exact dates', 'Provider names'].map((item) => (
                <div key={item} className="flex items-center gap-2">
                  <span className="text-red-400">×</span> {item}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Rewards */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-5xl mx-auto grid md:grid-cols-2 gap-12">
          <div>
            <h2 className="text-2xl font-bold mb-6">Rewards</h2>
            <p className="text-white/40 mb-6">Earn points for contributions</p>
            <div className="space-y-3">
              {[
                { action: 'Sign up', points: 100 },
                { action: 'Sign consent', points: 50 },
                { action: 'Connect records', points: 100 },
                { action: 'Data accessed', points: 10 },
              ].map((item) => (
                <div key={item.action} className="flex justify-between border-b border-white/10 pb-2 text-sm">
                  <span className="text-white/60">{item.action}</span>
                  <span className="text-emerald-400 font-mono">+{item.points}</span>
                </div>
              ))}
            </div>
            <p className="text-white/30 text-xs mt-4">100 pts = $1</p>
          </div>
          <div className="p-6 border border-white/10">
            <h3 className="font-medium mb-4">Redeem for</h3>
            <ul className="space-y-3 text-sm text-white/50">
              <li>Gift cards (Amazon, Visa)</li>
              <li>Charity donations</li>
              <li>Direct payment</li>
              <li>Medical bill credits</li>
            </ul>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold mb-8">FAQ</h2>
          <div className="space-y-4">
            {[
              { q: 'Do I need to have cancer?', a: 'Currently we focus on oncology data, but may expand.' },
              { q: 'How is data de-identified?', a: 'Cryptographic hashing removes all identifiable info.' },
              { q: 'Can I delete my data?', a: 'Yes, revoke consent anytime and data is removed in 30 days.' },
              { q: 'Who uses my data?', a: 'Vetted researchers with IRB approval.' },
            ].map((item, i) => (
              <div key={i} className="p-4 border border-white/10">
                <h3 className="font-medium mb-2">{item.q}</h3>
                <p className="text-sm text-white/40">{item.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 px-6 border-t border-white/5">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-3xl font-bold mb-4">Make a difference</h2>
          <p className="text-white/40 mb-8">Join patients helping advance cancer research</p>
          <Link to="/register?type=patient" className="px-8 py-3 bg-white text-black font-medium hover:bg-gray-100 transition-colors inline-block">
            Create Account
          </Link>
          <p className="text-white/30 text-sm mt-4">
            Already have an account? <Link to="/login" className="text-emerald-400 hover:underline">Sign in</Link>
          </p>
        </div>
      </section>
    </div>
  );
};

export default ForPatients;
