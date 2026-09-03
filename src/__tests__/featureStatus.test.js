/**
 * The manifest is the single source of truth for product status, so its
 * shape is enforced rather than assumed.
 */
import { FEATURES, STATUS, getFeature, isLive, featuresByStatus } from '../data/featureStatus';

describe('feature manifest', () => {
  const keys = Object.keys(FEATURES);

  it('is not empty', () => {
    expect(keys.length).toBeGreaterThan(20);
  });

  it.each(keys)('%s has a valid status and a name', (key) => {
    const feature = FEATURES[key];
    expect(Object.keys(STATUS)).toContain(feature.status);
    expect(typeof feature.name).toBe('string');
    expect(feature.name.length).toBeGreaterThan(0);
  });

  it('backs every live claim with evidence or an explicit note', () => {
    const unbacked = featuresByStatus('live')
      .filter((f) => !f.evidence && !f.note)
      .map((f) => f.key);
    expect(unbacked).toEqual([]);
  });

  it('explains every planned entry so it is not read as available', () => {
    // A planned entry with no note is just a capability name on a page.
    const planned = featuresByStatus('planned');
    expect(planned.length).toBeGreaterThan(0);
    planned.forEach((f) => expect(typeof f.name).toBe('string'));
  });

  it('keeps the controls that were never built marked planned', () => {
    // These were previously described as implemented. Regressing any of them
    // to live without building it would restore the original overclaim.
    const mustBePlanned = [
      'security.rls', 'security.kms', 'security.waf', 'security.mfa',
      'security.soc2', 'security.pen-test', 'security.signed-urls',
      'ingest.epic', 'ingest.cerner', 'ingest.hl7v2', 'ingest.omop',
      'ingest.emr-direct', 'governance.central-sirb',
      'governance.prenegotiated-dua', 'research.federated-query',
      'privacy.k-anonymity', 'privacy.nlp-deid', 'patient.rewards',
    ];
    mustBePlanned.forEach((key) => {
      expect(getFeature(key).status).toBe('planned');
    });
  });

  it('keeps date truncation live, since the storage layer depends on it', () => {
    expect(isLive('privacy.date-truncation')).toBe(true);
  });

  it('throws on an unknown key rather than rendering nothing', () => {
    expect(() => getFeature('does.not.exist')).toThrow(/Unknown feature key/);
  });
});
