import React from 'react';
import { Link } from 'react-router-dom';

const Section = ({ title, children }) => (
  <section className="mb-10">
    <h2 className="text-xl font-bold mb-4">{title}</h2>
    <div className="text-white/50 space-y-3 leading-relaxed">{children}</div>
  </section>
);

const Privacy = () => (
  <div className="min-h-screen bg-black text-white">
    <section className="py-24 px-6">
      <div className="max-w-3xl mx-auto">
        <p className="text-sm text-emerald-400 uppercase tracking-wider mb-4">Privacy</p>
        <h1 className="text-4xl md:text-5xl font-bold mb-4">Privacy Notice</h1>
        <p className="text-white/30 text-sm mb-12">
          This notice describes how the HealthDB platform handles the information you give it. It
          reflects how the software actually behaves, not an aspiration.
        </p>

        <Section title="What we deliberately do not store">
          <p>
            When you upload a FHIR export, it is de-identified before anything is written to the
            database. The platform strips the 18 HIPAA Safe Harbor identifier categories, including:
          </p>
          <ul className="list-disc list-inside space-y-1">
            <li>Names, and the names of relatives or employers</li>
            <li>Street addresses and geographic units smaller than a state; ZIP codes</li>
            <li>Telephone and fax numbers, email addresses, URLs and IP addresses</li>
            <li>Social Security numbers, medical record numbers, health plan and account numbers</li>
            <li>Certificate, licence, device and vehicle identifiers</li>
            <li>Biometric identifiers and full-face photographs</li>
            <li>Any other unique identifying number or code carried in the source record</li>
          </ul>
          <p>
            The raw uploaded bundle is parsed in memory and discarded. It is never persisted to disk
            or to the database.
          </p>
        </Section>

        <Section title="What is kept">
          <ul className="list-disc list-inside space-y-1">
            <li>Coded clinical facts: conditions, medications, procedures and laboratory results</li>
            <li>Age expressed as a band, with everyone over 89 collapsed into a single 90+ band</li>
            <li>Dates reduced to the year only — no month, no day</li>
            <li>Sex, and race/ethnicity where the source record contains it</li>
            <li>A per-study pseudonym, so the same person cannot be linked across studies</li>
          </ul>
          <p>
            Records are re-scanned after de-identification. If a residual identifier pattern is
            detected, the field is dropped rather than stored.
          </p>
        </Section>

        <Section title="Your account">
          <p>
            Your email address and name are stored so you can sign in and so we can contact you about
            your account. This account information is kept separate from clinical records and is
            never released to researchers. Passwords are stored only as a salted PBKDF2-SHA256 hash.
          </p>
        </Section>

        <Section title="Consent, and withdrawing it">
          <p>
            No researcher can see anything you contribute until you sign a consent covering that use.
            Consents are granular and are recorded with a timestamp and version.
          </p>
          <p>
            You can revoke any consent at any time from your patient portal. Revocation takes effect
            immediately: from that moment your data is excluded from cohort counts, analytics and any
            new export. Extracts already delivered to a researcher before revocation cannot be
            recalled, which is why every extract is de-identified.
          </p>
        </Section>

        <Section title="What researchers actually receive">
          <p>
            Researchers query aggregate counts and de-identified record-level data scoped to studies
            they are authorised for. Aggregate results are suppressed below a minimum cell size to
            prevent re-identification of small groups. Export access is checked on every request.
          </p>
        </Section>

        <Section title="Limits you should know about">
          <p>
            Safe Harbor de-identification is applied by automated rules. Free-text narrative fields
            can contain identifiers that pattern matching does not catch, so free text is not
            imported. Do not paste identifying details into any free-text field on this site.
          </p>
          <p>
            Handling identifiable patient data at scale additionally requires IRB review, executed
            data use agreements, and a business associate agreement with the hosting provider. Where
            those are not in place, the platform is restricted to de-identified data.
          </p>
        </Section>

        <Section title="Contact">
          <p>
            Questions about this notice, or a request to delete your account and contributed records:{' '}
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

export default Privacy;
