import React from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';

const ForPatients = () => {
  return (
    <div className="bg-black text-white min-h-screen">
      {/* Hero Section */}
      <section className="relative min-h-[80vh] flex items-center overflow-hidden pt-20">
        <div className="absolute inset-0 gradient-bg" />
        <div className="absolute inset-0 grid-pattern" />
        
        {/* Accent glow */}
        <div className="absolute top-1/3 right-0 w-[600px] h-[600px] bg-[#00d4aa]/10 rounded-full blur-[150px]" />

        <div className="relative z-10 max-w-6xl mx-auto px-6 grid lg:grid-cols-2 gap-16 items-center">
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
          >
            <p className="text-xs uppercase tracking-[0.3em] text-[#00d4aa] mb-4">
              For Patients
            </p>
            <h1 className="heading-display text-4xl md:text-5xl lg:text-6xl text-white mb-6">
              Your data can
              <br />
              <span className="text-white/60">advance cancer research</span>
            </h1>
            <p className="text-lg text-white/50 mb-8 leading-relaxed">
              Voluntarily contribute your de-identified medical data to help researchers 
              discover new treatments and improve outcomes for future patients.
            </p>
            <div className="flex flex-col sm:flex-row gap-4">
              <Link to="/register?type=patient" className="btn-primary">
                Join as Patient
              </Link>
              <a href="#how-it-works" className="btn-secondary">
                Learn More
              </a>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="hidden lg:block"
          >
            <div className="grid grid-cols-2 gap-4">
              {[
              ].map((item, index) => (
                <div
                  key={item.label}
                  className="card-glass p-6 text-center"
                >
                  
                  <p className="text-2xl font-light text-white mb-1">{item.value}</p>
                  <p className="text-white/40 text-sm">{item.label}</p>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Why Contribute */}
      <section className="py-24 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">
              Make a Difference
            </p>
            <h2 className="heading-display text-3xl md:text-4xl text-white/90">
              Why contribute your data?
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-px bg-white/5">
            {[
              {
                
                title: 'Advance Research',
                description: 'Your health journey data helps researchers understand cancer better, identify patterns, and develop more effective treatments.',
              },
              {
                
                title: 'Help Future Patients',
                description: 'The insights from your data may help doctors make better treatment decisions for patients facing similar diagnoses.',
              },
              {
                
                title: 'Earn Rewards',
                description: 'Receive points for contributing data that can be redeemed for gift cards, donations to cancer charities, or direct payments.',
              },
            ].map((item, index) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="card-glass p-10"
              >
                
                <h3 className="text-xl font-medium text-white mb-4">{item.title}</h3>
                <p className="text-white/40 text-sm leading-relaxed">{item.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="py-24 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-20">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">
                Simple Process
              </p>
              <h2 className="heading-display text-3xl md:text-4xl text-white/90 mb-6">
                How it works
              </h2>
              <p className="text-white/40 text-lg leading-relaxed mb-8">
                Contributing your data is completely voluntary. You control what you share 
                and can revoke access at any time. Your privacy is our top priority.
              </p>
              <Link to="/register?type=patient" className="btn-primary inline-block">
                Get Started
              </Link>
            </motion.div>

            <div className="space-y-6">
              {[
                {
                  step: '01',
                  title: 'Create Account',
                  description: 'Sign up for a free patient account. No medical records required upfront.',
                },
                {
                  step: '02',
                  title: 'Review & Sign Consent',
                  description: 'Read our clear consent forms explaining exactly what data will be shared and how it will be used.',
                },
                {
                  step: '03',
                  title: 'Connect Your Records',
                  description: 'Securely link your medical records from hospitals using MyChart, Cerner, or manual upload.',
                },
                {
                  step: '04',
                  title: 'Data De-identified',
                  description: 'Your data is automatically de-identified - your name, SSN, and exact dates are never shared.',
                },
                {
                  step: '05',
                  title: 'Contribute & Earn',
                  description: 'Your anonymized data helps research. Earn points when researchers access your contributions.',
                },
              ].map((item, index) => (
                <motion.div
                  key={item.step}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  viewport={{ once: true }}
                  className="flex gap-5 group"
                >
                  <span className="text-2xl font-light text-white/20 group-hover:text-[#00d4aa]/50 transition-colors">
                    {item.step}
                  </span>
                  <div>
                    <h3 className="text-lg font-medium text-white mb-1">{item.title}</h3>
                    <p className="text-white/40 text-sm">{item.description}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Privacy & Security */}
      <section className="py-24 px-6 border-t border-white/5 bg-gradient-to-b from-transparent to-[#00d4aa]/5">
        <div className="max-w-6xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-center mb-16"
          >
            <p className="text-xs uppercase tracking-[0.3em] text-white/40 mb-4">
              Your Privacy Matters
            </p>
            <h2 className="heading-display text-3xl md:text-4xl text-white/90">
              How we protect your data
            </h2>
          </motion.div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              {
                
                title: 'HIPAA Compliant',
                description: 'We follow strict healthcare privacy regulations.',
              },
              {
                
                title: 'De-identification',
                description: 'Your identity is cryptographically protected.',
              },
              {
                
                title: 'Your Control',
                description: 'Revoke consent and delete data anytime.',
              },
              {
                
                title: 'Full Transparency',
                description: 'See exactly who accessed your data.',
              },
            ].map((item, index) => (
              <motion.div
                key={item.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="text-center p-6"
              >
                
                <h3 className="text-white font-medium mb-2">{item.title}</h3>
                <p className="text-white/40 text-sm">{item.description}</p>
              </motion.div>
            ))}
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.3 }}
            viewport={{ once: true }}
            className="mt-12 card-glass p-8 max-w-3xl mx-auto"
          >
            <h3 className="text-white font-medium mb-4 text-lg">What is NOT shared:</h3>
            <div className="grid sm:grid-cols-2 gap-4 text-sm">
              {[
                'Your full name',
                'Social Security Number',
                'Exact birth date (only age range)',
                'Home address',
                'Phone number',
                'Email address',
                'Exact treatment dates (only month/year)',
                'Provider names',
              ].map((item) => (
                <div key={item} className="flex items-center gap-2 text-white/60">
                  <svg className="w-4 h-4 text-red-400 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  {item}
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Rewards */}
      <section className="py-24 px-6 border-t border-white/5">
        <div className="max-w-6xl mx-auto">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
            >
              <p className="text-xs uppercase tracking-[0.3em] text-[#00d4aa] mb-4">
                Rewards Program
              </p>
              <h2 className="heading-display text-3xl md:text-4xl text-white/90 mb-6">
                Earn while you contribute
              </h2>
              <p className="text-white/40 text-lg leading-relaxed mb-8">
                We believe patients should be compensated for their valuable contributions 
                to medical research. Earn points for every action and redeem them for real rewards.
              </p>
              <div className="space-y-4">
                {[
                  { action: 'Sign up bonus', points: 100 },
                  { action: 'Sign a consent', points: 50 },
                  { action: 'Connect medical records', points: 100 },
                  { action: 'Data accessed by researcher', points: 10 },
                ].map((item) => (
                  <div key={item.action} className="flex items-center justify-between border-b border-white/10 pb-3">
                    <span className="text-white/70">{item.action}</span>
                    <span className="text-[#00d4aa] font-mono">+{item.points} pts</span>
                  </div>
                ))}
              </div>
              <p className="text-white/30 text-sm mt-6">100 points = $1.00 value</p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              viewport={{ once: true }}
              className="card-glass p-8"
            >
              <h3 className="text-white font-medium mb-6">Redeem your points for:</h3>
              <div className="space-y-4">
                {[
                  {  title: 'Gift Cards', desc: 'Amazon, Visa, and more' },
                  {  title: 'Charity Donations', desc: 'American Cancer Society, St. Jude' },
                  {  title: 'Direct Payment', desc: 'PayPal or bank transfer' },
                  {  title: 'Medical Bill Credits', desc: 'Apply to your healthcare costs' },
                ].map((item) => (
                  <div key={item.title} className="flex items-center gap-4 p-3 bg-white/5 rounded">
                    
                    <div>
                      <p className="text-white font-medium">{item.title}</p>
                      <p className="text-white/40 text-sm">{item.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-24 px-6 border-t border-white/5">
        <div className="max-w-3xl mx-auto">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
            className="text-center mb-12"
          >
            <h2 className="heading-display text-3xl md:text-4xl text-white/90">
              Frequently Asked Questions
            </h2>
          </motion.div>

          <div className="space-y-6">
            {[
              {
                q: 'Do I need to have cancer to participate?',
                a: 'Currently, we focus on oncology data, so we are looking for patients who have been diagnosed with cancer. However, we may expand to other conditions in the future.',
              },
              {
                q: 'How is my data de-identified?',
                a: 'We use cryptographic hashing to remove all personally identifiable information. Your name, SSN, exact dates, and contact information are never stored or shared. Only aggregate patterns are used for research.',
              },
              {
                q: 'Can I delete my data?',
                a: 'Yes! You can revoke consent and request data deletion at any time through your patient portal. We will remove your data within 30 days.',
              },
              {
                q: 'Who uses my data?',
                a: 'Only vetted researchers from academic institutions and pharmaceutical companies who have IRB approval for their studies. You can see a log of all access in your portal.',
              },
              {
                q: 'Is this legal and safe?',
                a: 'Absolutely. We are fully HIPAA compliant and follow all federal regulations for protected health information. Your consent is required for any data sharing.',
              },
            ].map((item, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: index * 0.1 }}
                viewport={{ once: true }}
                className="card-glass p-6"
              >
                <h3 className="text-white font-medium mb-2">{item.q}</h3>
                <p className="text-white/40 text-sm leading-relaxed">{item.a}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 px-6 border-t border-white/5">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            viewport={{ once: true }}
          >
            <h2 className="heading-display text-3xl md:text-4xl lg:text-5xl text-white/90 mb-6">
              Ready to make a difference?
            </h2>
            <p className="text-white/40 text-lg mb-10 max-w-xl mx-auto">
              Join thousands of patients who are helping advance cancer research 
              while earning rewards for their contributions.
            </p>
            <Link to="/register?type=patient" className="btn-primary text-lg px-10 py-4">
              Create Patient Account
            </Link>
            <p className="text-white/30 text-sm mt-6">
              Already have an account? <Link to="/login" className="text-[#00d4aa] hover:underline">Sign in</Link>
            </p>
          </motion.div>
        </div>
      </section>
    </div>
  );
};

export default ForPatients;
