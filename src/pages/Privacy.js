import React from 'react';
import { Link } from 'react-router-dom';

const Section = ({ title, children }) => (
  <section className="mb-10">
    <h2 className="text-xl font-medium mb-4">{title}</h2>
    <div className="text-white/50 space-y-3 leading-relaxed">{children}</div>
  </section>
);

const Privacy = () => (
  <div className="min-h-screen bg-black text-white">
    <section className="py-24 px-6">
      <div className="max-w-3xl mx-auto">
        <p className="text-xs text-emerald-300 uppercase tracking-[0.2em] mb-4">Privacy · pilot notice</p>
        <h1 className="text-4xl md:text-5xl font-medium mb-4">What this prototype may collect</h1>
        <p className="text-white/35 text-sm mb-12">Updated September 5, 2026</p>

        <div className="border border-amber-400/20 bg-amber-400/5 p-5 mb-12 text-sm text-amber-100/80">
          Do not submit protected health information, patient identifiers, or real medical records.
          HealthDB is not operating as a production clinical-data service.
        </div>

        <Section title="Scope">
          <p>
            This notice covers the public HealthDB website and invite-only technical pilot. The pilot
            is intended for workflow evaluation with synthetic data. It has no production EHR
            integrations, institutional data agreements, or third-party compliance certifications.
          </p>
        </Section>

        <Section title="Information you provide">
          <ul className="list-disc list-inside space-y-1">
            <li>Contact requests: name, email, organization, area of interest, and message</li>
            <li>Invited accounts: name, email, organization, role, and password hash</li>
            <li>Pilot activity: synthetic cohort, study, consent, and workflow records you create</li>
          </ul>
          <p>Contact forms are general inquiry channels. Do not use them for clinical information or medical advice.</p>
        </Section>

        <Section title="Technical information">
          <p>
            The service may process standard request information needed to operate and secure the
            site, such as timestamps, requested routes, response status, and network address. Access
            to pilot workspaces is also logged for troubleshooting and security review.
          </p>
        </Section>

        <Section title="Synthetic-data workspace">
          <p>
            Some invited accounts can exercise prototype FHIR, consent, cohort, and extraction
            workflows. These controls are not authorization to upload real records. Production is
            configured to block self-service registration and record upload unless the pilot operator
            deliberately enables those features for a controlled test.
          </p>
        </Section>

        <Section title="Use and disclosure">
          <p>
            Information is used to respond to inquiries, administer invited access, test the product,
            diagnose failures, and protect the service. Infrastructure providers may process data as
            needed to host and operate the application. HealthDB does not offer pilot contact or
            account information as a research dataset.
          </p>
        </Section>

        <Section title="Security and retention limits">
          <p>
            Passwords are stored as salted password hashes. Role checks are enforced by the API, and
            sensitive workspaces require authentication. No security measure eliminates risk, and
            these controls have not been represented as independently certified.
          </p>
          <p>
            A public retention schedule has not yet been established. Until one is published, avoid
            entering information you do not want retained and contact us to request account or inquiry deletion.
          </p>
        </Section>

        <Section title="Questions or deletion requests">
          <p>
            Use the <Link to="/contact" className="text-emerald-300 hover:underline">contact form</Link>{' '}
            and do not include patient information in the request.
          </p>
        </Section>
      </div>
    </section>
  </div>
);

export default Privacy;
