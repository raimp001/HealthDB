import React from 'react';
import { Link } from 'react-router-dom';

const Section = ({ title, children }) => (
  <section className="mb-10">
    <h2 className="text-xl font-medium mb-4">{title}</h2>
    <div className="text-white/50 space-y-3 leading-relaxed">{children}</div>
  </section>
);

const Terms = () => (
  <div className="min-h-screen bg-black text-white">
    <section className="py-24 px-6">
      <div className="max-w-3xl mx-auto">
        <p className="text-xs text-emerald-300 uppercase tracking-[0.2em] mb-4">Terms · closed pilot</p>
        <h1 className="text-4xl md:text-5xl font-medium mb-4">Terms of pilot use</h1>
        <p className="text-white/35 text-sm mb-12">Updated September 5, 2026</p>

        <Section title="What HealthDB is today">
          <p>
            HealthDB is an early software prototype for evaluating oncology research-data workflows
            with synthetic information. It is not a healthcare provider, medical device, clinical
            decision tool, production data repository, IRB, or compliance service.
          </p>
        </Section>

        <Section title="Invite-only access">
          <p>
            Public account creation is closed. An invitation allows you to evaluate the prototype; it
            does not grant access to real patient data, production datasets, clinical services, or an
            institutional partnership.
          </p>
        </Section>

        <Section title="Synthetic data only">
          <ul className="list-disc list-inside space-y-1">
            <li>Do not enter or upload protected health information or patient identifiers.</li>
            <li>Do not upload real medical records, portal exports, or institutional datasets.</li>
            <li>Use only fictional or explicitly authorized synthetic test content.</li>
            <li>Do not rely on pilot output for patient care, research conclusions, or regulatory submissions.</li>
          </ul>
        </Section>

        <Section title="Account security and acceptable use">
          <p>
            Keep credentials confidential and notify HealthDB if access may be compromised. Do not
            probe another user's data, bypass role or study boundaries, interfere with the service,
            or use pilot output to attempt re-identification.
          </p>
        </Section>

        <Section title="Prototype consent and regulatory screens">
          <p>
            Consent forms, regulatory records, agreement states, audit events, and approvals shown in
            the pilot are software simulations. They do not create legal consent, IRB approval, a DUA,
            a BAA, site reliance, or any other institutional authorization.
          </p>
        </Section>

        <Section title="No rewards, datasets, or service commitment">
          <p>
            HealthDB does not currently promise participant compensation, sell datasets, publish a
            price list, guarantee uptime, or commit to a support or delivery timeline. Pilot access may
            change or end as the product is evaluated.
          </p>
        </Section>

        <Section title="No warranty">
          <p>
            The prototype is provided as is and may be incomplete, inaccurate, or unavailable. You are
            responsible for independently reviewing any workflow, security control, or output before
            considering it for real-world use.
          </p>
        </Section>

        <Section title="Questions">
          <p>
            Use the <Link to="/contact" className="text-emerald-300 hover:underline">contact form</Link>{' '}
            and do not include patient information.
          </p>
        </Section>
      </div>
    </section>
  </div>
);

export default Terms;
