import React from 'react';
import { Link } from 'react-router-dom';

const Section = ({ title, children }) => (
  <section className="mb-10">
    <h2 className="text-xl font-bold mb-4">{title}</h2>
    <div className="text-white/50 space-y-3 leading-relaxed">{children}</div>
  </section>
);

const Terms = () => (
  <div className="min-h-screen bg-black text-white">
    <section className="py-24 px-6">
      <div className="max-w-3xl mx-auto">
        <p className="text-sm text-emerald-400 uppercase tracking-wider mb-4">Terms</p>
        <h1 className="text-4xl md:text-5xl font-bold mb-4">Terms of Use</h1>
        <p className="text-white/50 text-sm mb-12">
          By creating an account you agree to the terms below.
        </p>

        <Section title="What the platform is">
          <p>
            HealthDB is research infrastructure. It lets patients contribute de-identified records
            under explicit consent, and lets approved researchers query those records across
            institutions. It is not a medical device, not a diagnostic tool, and not a source of
            clinical advice.
          </p>
        </Section>

        <Section title="If you are a patient">
          <ul className="list-disc list-inside space-y-1">
            <li>Only upload records that are your own, or that you are legally authorised to share.</li>
            <li>Participation is voluntary and does not affect the care you receive anywhere.</li>
            <li>You may revoke any consent at any time from your portal.</li>
            <li>
              Contributing does not enrol you in a clinical trial. Study enrolment is a separate,
              explicit step.
            </li>
          </ul>
        </Section>

        <Section title="If you are a researcher">
          <ul className="list-disc list-inside space-y-1">
            <li>
              You must not attempt to re-identify any individual, link records to an external
              identified dataset, or contact a contributor.
            </li>
            <li>
              You must hold the IRB approval or documented exemption that your use requires, and any
              applicable data use agreement, before requesting an export.
            </li>
            <li>
              Data you receive may be used only for the study it was released under. Redistribution
              outside your approved study team is prohibited.
            </li>
            <li>
              You must not circumvent small-cell suppression, including by combining queries to
              isolate an individual.
            </li>
            <li>Access is logged. Violations end access and may be reported to your institution.</li>
          </ul>
        </Section>

        <Section title="If you are an institution">
          <p>
            Institutional accounts can register protocols, record reliance agreements and approve
            cross-site collaborations. Recording an agreement on this platform is an administrative
            record — it does not replace your own legal execution of that agreement.
          </p>
        </Section>

        <Section title="Accounts">
          <p>
            Keep your credentials confidential and tell us promptly if you believe an account has
            been compromised. Do not share logins. We may suspend an account that is being used in a
            way that puts contributors at risk.
          </p>
        </Section>

        <Section title="No warranty">
          <p>
            The platform is provided as is. Research data may be incomplete, inconsistently coded, or
            biased by who chose to contribute. You are responsible for assessing fitness for your
            analysis. Nothing here should be relied on for clinical decision-making.
          </p>
        </Section>

        <Section title="Changes">
          <p>
            We may update these terms. Material changes affecting how contributed data may be used
            will be surfaced to you, and where consent is affected we will ask you to re-consent
            rather than assume it.
          </p>
        </Section>

        <Section title="Contact">
          <p>
            Questions about these terms:{' '}
            <Link to="/contact" className="text-emerald-400 hover:underline">
              get in touch
            </Link>
            .
          </p>
        </Section>
      </div>
    </section>
  </div>
);

export default Terms;
