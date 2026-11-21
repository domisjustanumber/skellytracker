import type { SkellyDocsConfig } from '@freemocap/skellydocs';

// This site runs in docs-only mode (no marketing landing page), so this config
// now feeds only the Roadmap page (src/pages/roadmap.tsx):
//   - `projectBoardUrl` is the GitHub project board it renders
//   - `collectLinkedUrls(config)` scans `features`/`guarantees` issue links to pin
// `hero`/`features` are intentionally minimal.
const config: SkellyDocsConfig = {
  hero: {
    title: 'skellytracker',
    accentedSuffix: 'tracker',
    subtitle: 'The tracking backend for FreeMoCap',
    tagline:
      'Pipelines, detectors and execution providers for keypoint tracking',
    logoSrc: '/skellytracker/img/logo.svg',
    parentProject: {
      name: 'FreeMoCap',
      url: 'https://freemocap.org',
    },
    ctaButtons: [
      { label: 'Get Started', to: '/', variant: 'primary' },
      { label: 'View on GitHub', to: 'https://github.com/freemocap/skellytracker', variant: 'secondary' },
    ],
  },

  features: [],

  // Consumed by collectLinkedUrls() on the Roadmap page (must be an array).
  guaranteeIssues: [],

  guaranteesConfig: {
    title: <>skellytracker guarantees:</>,
    items: [],
    issues: [],
  },

  // TODO(verify): confirm this points at skellytracker's board (scaffold default was /projects/32).
  projectBoardUrl: 'https://github.com/orgs/freemocap/projects/32',
};

export default config;
