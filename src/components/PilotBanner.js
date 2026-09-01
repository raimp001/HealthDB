import React from 'react';

/**
 * Site-wide status strip. HealthDB holds no compliance certifications and has
 * no institutional agreements in place, so every page has to say so rather
 * than relying on the visitor to find the disclosure.
 */
const PilotBanner = () => (
  <div className="bg-amber-400/10 border-b border-amber-400/20 px-4 py-1.5 text-center">
    {/* Short on phones so the strip stays one line and the bar below keeps
        its height; the full sentence appears once there is room for it. */}
    <p className="text-[11px] leading-tight text-amber-400/90 sm:hidden">
      Closed pilot — not for clinical use.
    </p>
    <p className="hidden sm:block text-xs text-amber-400/90">
      Closed pilot — not for clinical use. HealthDB holds no compliance
      certifications and does not accept real patient data.
    </p>
  </div>
);

export default PilotBanner;
