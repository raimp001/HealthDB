import React from 'react';

/**
 * Site-wide status strip. HealthDB holds no compliance certifications and has
 * no institutional agreements in place, so every page has to say so rather
 * than relying on the visitor to find the disclosure.
 */
const PilotBanner = () => (
  <div className="mt-20 bg-amber-950/95 border-y border-amber-400/20 px-6 py-2 text-center">
    <p className="text-xs text-amber-200">
      Closed technical pilot · Synthetic data only · No clinical use, PHI, or compliance certifications
    </p>
  </div>
);

export default PilotBanner;
