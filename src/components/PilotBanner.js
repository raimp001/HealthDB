import React from 'react';

/**
 * Site-wide status strip. HealthDB holds no compliance certifications and has
 * no institutional agreements in place, so every page has to say so rather
 * than relying on the visitor to find the disclosure.
 *
 * One paragraph, not two. An earlier version rendered a short phone copy and
 * a full desktop copy as separate elements, so "Closed pilot" existed twice in
 * the DOM with one of them always hidden. Anything selecting the first match —
 * a test, a screen reader running the page, a browser's find-in-page — could
 * land on the hidden one. Only the trailing detail varies by width now.
 */
const PilotBanner = () => (
  <div className="bg-amber-400/10 border-b border-amber-400/20 px-4 py-1.5 text-center">
    <p className="text-[11px] sm:text-xs leading-tight text-amber-400/90">
      Closed pilot — not for clinical use.
      <span className="hidden sm:inline">
        {' '}HealthDB holds no compliance certifications and does not accept
        real patient data.
      </span>
    </p>
  </div>
);

export default PilotBanner;
