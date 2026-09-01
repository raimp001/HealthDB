import React from 'react';
import { Link } from 'react-router-dom';

/**
 * These pages describe an intended architecture, most of which is not built.
 * Supabase RLS, AWS KMS, Kong, WAF, MFA, OMOP CDM, NLP de-identification,
 * k-anonymity verification and signed URLs appear nowhere in the codebase.
 * Presenting them as the current security posture would misrepresent the
 * platform to anyone assessing it, so every one of these pages says so first.
 */
const TargetArchitectureBanner = ({ implemented = [], planned = [] }) => (
  <div className="border border-amber-400/30 bg-amber-400/5 p-6 mb-10">
    <div className="flex items-start gap-3 mb-4">
      <span className="text-amber-400 text-lg leading-none">⚠</span>
      <div>
        <p className="text-amber-400 font-medium mb-1">
          Target architecture — not the deployed system
        </p>
        <p className="text-white/50 text-sm">
          This page describes where HealthDB is heading. Most of it is not built.
          The running application is a FastAPI and SQLAlchemy service; it does not
          use Supabase, AWS KMS, an API gateway, a WAF, MFA, or OMOP CDM. Do not
          treat this page as evidence of any security control.
        </p>
      </div>
    </div>

    {(implemented.length > 0 || planned.length > 0) && (
      <div className="grid md:grid-cols-2 gap-6 mt-6 pt-6 border-t border-amber-400/20">
        <div>
          <p className="text-xs text-emerald-400/80 uppercase tracking-wider mb-2">
            Built today
          </p>
          <ul className="space-y-1">
            {implemented.map((item) => (
              <li key={item} className="text-sm text-white/60">✓ {item}</li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-xs text-amber-400/80 uppercase tracking-wider mb-2">
            Not built
          </p>
          <ul className="space-y-1">
            {planned.map((item) => (
              <li key={item} className="text-sm text-white/40">◦ {item}</li>
            ))}
          </ul>
        </div>
      </div>
    )}

    <p className="text-xs text-white/30 mt-6">
      For what is actually implemented, see{' '}
      <Link to="/institutions" className="text-white/50 hover:text-white underline">
        Security &amp; Compliance
      </Link>.
    </p>
  </div>
);

export default TargetArchitectureBanner;
