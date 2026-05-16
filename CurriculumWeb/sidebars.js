// @ts-check

// This runs in Node.js - Don't use client-side code here (browser APIs, JSX...)

/**
 * Creating a sidebar enables you to:
 - create an ordered group of docs
 - render a sidebar for each doc of that group
 - provide next/previous navigation

 The sidebars can be generated from the filesystem, or explicitly defined here.

 Create as many sidebars as you want.

 @type {import('@docusaurus/plugin-content-docs').SidebarsConfig}
 */
const sidebars = {
  curriculumSidebar: [
    'intro',
    {
      type: 'category',
      label: 'MVP Path: State, Change, Symmetry',
      items: [
        'wiki/what-is-physics-looking-for',
        'wiki/what-is-a-state',
        'wiki/change-rules',
        'wiki/symmetry-change-that-does-not-matter',
        'wiki/conservation-memory-of-symmetry',
        'wiki/energy-time-sameness',
        'wiki/where-this-path-leads',
      ],
    },
    {
      type: 'category',
      label: 'Optional Math Lens',
      items: [
        'math/coordinates',
        'math/functions-as-rules',
        'math/tiny-noether-preview',
      ],
    },
    {
      type: 'category',
      label: 'Draft Doorways',
      items: [
        'wiki/discrete-vs-continuous',
        'wiki/the-speed-of-causality',
        'wiki/geodesics-and-gravity',
        'wiki/wave-particle-duality',
        'wiki/superposition-and-acoustics',
        'wiki/space-occupiers-vs-messengers',
      ],
    },
  ],
};

export default sidebars;
