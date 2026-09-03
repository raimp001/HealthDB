import React from 'react';
import { STATUS, getFeature } from '../data/featureStatus';

/**
 * Renders a feature's real state next to any claim about it.
 *
 * Takes a manifest key rather than a literal status, so a badge can never
 * drift from what src/data/featureStatus.js says. An unknown key throws at
 * render rather than silently showing nothing.
 */
const StatusBadge = ({ featureKey, size = 'sm', showNote = false }) => {
  const feature = getFeature(featureKey);
  const status = STATUS[feature.status];
  const padding = size === 'xs' ? 'px-1.5 py-0.5 text-[10px]' : 'px-2 py-0.5 text-xs';

  return (
    <span className="inline-flex items-center gap-2 align-middle">
      <span
        className={`inline-block border uppercase tracking-wider ${padding} ${status.className}`}
        title={feature.note || status.description}
      >
        {status.label}
      </span>
      {showNote && feature.note && (
        <span className="text-xs text-white/50">{feature.note}</span>
      )}
    </span>
  );
};

/** A labelled row: feature name, its badge, and the caveat that goes with it. */
export const StatusRow = ({ featureKey }) => {
  const feature = getFeature(featureKey);
  return (
    <div className="flex flex-wrap items-start justify-between gap-3 py-3 border-b border-white/5 last:border-0">
      <div className="min-w-0 flex-1">
        <div className="text-sm text-white/80">{feature.name}</div>
        {feature.note && <p className="text-xs text-white/50 mt-1">{feature.note}</p>}
        {feature.evidence && (
          <p className="text-xs text-white/35 mt-1 font-mono break-all">{feature.evidence}</p>
        )}
      </div>
      <StatusBadge featureKey={featureKey} />
    </div>
  );
};

export default StatusBadge;
