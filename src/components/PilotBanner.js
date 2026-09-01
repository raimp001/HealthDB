import React from 'react';

/**
 * Site-wide status strip. HealthDB holds no compliance certifications and has
 * no institutional agreements in place, so every page has to say so rather
 * than relying on the visitor to find the disclosure.
 */
const PilotBanner = () => (
  <div className="bg-amber-400/10 border-b border-amber-400/20 px-6 py-2 text-center">
    <p className="text-xs text-amber-400/90">
      Closed pilot — not for clinical use. HealthDB holds no compliance
      certifications and does not accept real patient data.
    </p>
  </div>
);

export default PilotBanner;
