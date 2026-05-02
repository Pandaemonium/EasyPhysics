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
    {
      type: 'category',
      label: 'Module 1: The Symmetries of Nature',
      items: ['wiki/discrete-vs-continuous'],
    },
    {
      type: 'category',
      label: 'Module 2: The Geometry of Spacetime',
      items: [
        'wiki/the-speed-of-causality',
        'wiki/geodesics-and-gravity',
      ],
    },
    {
      type: 'category',
      label: 'Module 3: Granular Waves',
      items: [
        'wiki/wave-particle-duality',
        'wiki/superposition-and-acoustics',
      ],
    },
    {
      type: 'category',
      label: 'Module 4: The Network of Fields',
      items: ['wiki/space-occupiers-vs-messengers'],
    },
  ],
};

export default sidebars;
