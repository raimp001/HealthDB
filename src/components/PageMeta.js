import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

const SITE = 'https://www.healthdb.ai';
const SUFFIX = 'HealthDB';

/**
 * Per-route document metadata for a single-page app.
 *
 * The app ships one index.html, so without this every route shares the
 * homepage's title, description and canonical URL, and private dashboards are
 * indexable. Private routes get `noindex, nofollow`.
 */
export const ROUTE_META = {
  '/': {
    title: 'Consented oncology research cohorts',
    description: 'A closed-pilot platform for building consented oncology research cohorts from patient-contributed records.',
  },
  '/patients': {
    title: 'For patients',
    description: 'Contribute your health records to cancer research with granular consent you can revoke at any time, and a log of every access.',
  },
  '/researchers': {
    title: 'For researchers',
    description: 'Build cohorts against de-identified pilot data, draft IRB protocols, and track study records.',
  },
  '/institutions': {
    title: 'For institutions',
    description: 'What HealthDB implements today for security and privacy, and what is not yet in place.',
  },
  '/status': {
    title: 'Platform status',
    description: 'What HealthDB does today, what runs only in the closed pilot, and what is not built.',
  },
  '/platform': {
    title: 'Platform roadmap',
    description: 'The infrastructure HealthDB intends to build. Most of it is not built yet.',
  },
  '/security-posture': {
    title: 'Target security architecture',
    description: 'The security architecture HealthDB is working toward. Not a description of the deployed system.',
  },
  '/data-flow': {
    title: 'Target data flow',
    description: 'The intended pipeline from record upload through de-identified export.',
  },
  '/repo-analyzer': {
    title: 'Target module map',
    description: 'Intended module boundaries, data sources and authorization boundaries.',
  },
  '/marketplace': {
    title: 'Data marketplace',
    description: 'Research datasets available through HealthDB. No datasets are currently available.',
  },
  '/resources': {
    title: 'Resources',
    description: 'Articles on de-identification, consent-based governance and multi-centre research.',
  },
  '/pricing': { title: 'Pricing', description: 'Access tiers for researchers and institutions during the closed pilot.' },
  '/about': { title: 'About', description: 'Why HealthDB exists, what is built, and what is planned.' },
  '/contact': { title: 'Contact', description: 'Get in touch about a pilot, access, or a data question.' },
  '/privacy': { title: 'Privacy policy', description: 'How HealthDB handles contributed health data.' },
  '/terms': { title: 'Terms of service', description: 'Terms governing use of the HealthDB closed pilot.' },
  '/cohort-builder': { title: 'Cohort builder', description: 'Build and size a research cohort.' },

  // Private or transactional. Never indexed.
  '/login': { title: 'Sign in', noindex: true },
  '/register': { title: 'Create an account', noindex: true },
  '/reset-password': { title: 'Reset your password', noindex: true },
  '/verify-email': { title: 'Verify your email', noindex: true },
  '/patient': { title: 'Patient portal', noindex: true },
  '/research': { title: 'Researcher dashboard', noindex: true },
  '/institution': { title: 'Institution dashboard', noindex: true },
};

/** Public, indexable routes — the sitemap generator reads this. */
export const PUBLIC_ROUTES = Object.entries(ROUTE_META)
  .filter(([, meta]) => !meta.noindex)
  .map(([path]) => path);

function upsert(selector, attrs) {
  let el = document.head.querySelector(selector);
  if (!el) {
    el = document.createElement(attrs.rel ? 'link' : 'meta');
    document.head.appendChild(el);
  }
  Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
  return el;
}

const PageMeta = () => {
  const { pathname } = useLocation();

  useEffect(() => {
    const meta = ROUTE_META[pathname] || {
      title: 'Page not found',
      description: 'That page does not exist.',
      noindex: true,
    };

    document.title = `${meta.title} · ${SUFFIX}`;

    if (meta.description) {
      upsert('meta[name="description"]', { name: 'description', content: meta.description });
      upsert('meta[property="og:description"]', { property: 'og:description', content: meta.description });
      upsert('meta[name="twitter:description"]', { name: 'twitter:description', content: meta.description });
    }
    upsert('meta[property="og:title"]', { property: 'og:title', content: `${meta.title} · ${SUFFIX}` });
    upsert('meta[name="twitter:title"]', { name: 'twitter:title', content: `${meta.title} · ${SUFFIX}` });
    upsert('meta[property="og:url"]', { property: 'og:url', content: `${SITE}${pathname}` });
    upsert('link[rel="canonical"]', { rel: 'canonical', href: `${SITE}${pathname}` });

    // Private and unknown routes must not be indexed.
    const robots = document.head.querySelector('meta[name="robots"]');
    if (meta.noindex) {
      upsert('meta[name="robots"]', { name: 'robots', content: 'noindex, nofollow' });
    } else if (robots) {
      robots.setAttribute('content', 'index, follow');
    }
  }, [pathname]);

  return null;
};

export default PageMeta;
