# Docusaurus Architecture Plan: Accessible Physics Curriculum

## 1. Why Docusaurus?

Docusaurus is a modern static site generator maintained by Meta. It is the ideal infrastructure for the Accessible Physics project for three primary reasons:

1. **MDX Support (Markdown + React):** Docusaurus parses `.mdx` files, allowing us to embed interactive React components directly inside standard Markdown text. This provides a native, elegant solution for the "hover-over glossary" requirement without breaking the writing flow.
2. **Git-Native Agentic Workflow:** Unlike Notion or BookStack, all content in Docusaurus lives as plain text files in a GitHub repository. AI Agents (Writer and Evaluator) can natively read, diff, edit, and commit curriculum changes using standard file I/O operations.
3. **Hierarchical Sidebars:** It automatically generates collapsible, hierarchical navigation sidebars from folder structures, perfectly mapping to our pedagogical module sequence.

---

## 2. Project Directory Structure

The Docusaurus application will live alongside the Lean formalization in the repository, ensuring the physics axioms and the pedagogy remain version-controlled together.

```text
c:\Projects\StandardModel\
├── PhysicsSM/                 # Lean 4 Formalization
├── AgentTasks/                # AI Agent Prompts and Jobs
└── CurriculumWeb/             # Docusaurus Root
    ├── docs/                  # Core Curriculum Content (.mdx)
    │   ├── 01-Symmetries/     # Module 1
    │   ├── 02-Spacetime/      # Module 2
    │   ├── 03-Quantum/        # Module 3
    │   └── 04-StandardModel/  # Module 4
    ├── src/
    │   ├── components/        # React Components (e.g., GlossaryHover.js)
    │   └── css/               # Custom Styling (Accessibility, High Contrast)
    ├── static/                # Images, Diagrams, Feynman graphics
    ├── docusaurus.config.js   # Site configuration
    └── sidebars.js            # Navigation hierarchy mapping
```

---

## 3. The Dual-Nomenclature Engine (MDX Glossary)

To support the strict lexical mapping without causing cognitive overload, we will build a global React component named `<Term />`. 

### The Component (`src/components/Term.js`)
This component will accept two props: the intuitive term and the historical jargon. When hovered, it will display a clean, accessible tooltip.

```jsx
import React from 'react';
import Tooltip from '@theme/Tooltip'; // Docusaurus/Infima native tooltip

export default function Term({ intuitive, jargon, definition }) {
  return (
    <Tooltip 
      content={<span><b>{jargon}:</b> {definition}</span>} 
      placement="top"
    >
      <span className="glossary-term" tabIndex="0">
        {intuitive}
      </span>
    </Tooltip>
  );
}
```

### Usage in Markdown (`docs/04-StandardModel/01-space-occupiers.mdx`)
The AI Writer Agent will be instructed to use this component whenever introducing a mapped term.

```mdx
import Term from '@site/src/components/Term';

# The Foundation of Matter

The universe is filled with particles that refuse to overlap. We call these 
<Term 
  intuitive="Space-Occupiers" 
  jargon="Fermions" 
  definition="Particles governed by the Pauli Exclusion Principle that provide the physical volume of matter." 
/>. Because they resist sharing the same state, they give rigid structure to everything you can touch.
```

---

## 4. Content Architecture & Pedagogical Sequence

The `sidebars.js` file will strictly enforce the "Symmetry-First" pedagogical sequence.

1. **Module 1: The Symmetries of Nature** (`docs/01-Symmetries/`)
   - 01-discrete-vs-continuous.mdx
   - 02-noethers-theorem.mdx (Energy, Momentum, Angular Momentum)
   - 03-discrete-symmetries.mdx (Charge, Parity, Time)
2. **Module 2: The Geometry of Spacetime** (`docs/02-Spacetime/`)
   - 01-the-speed-of-causality.mdx
   - 02-invariant-intervals.mdx
   - 03-geodesics-and-gravity.mdx (The Rubber Sheet)
3. **Module 3: Granular Waves** (`docs/03-Quantum/`)
   - 01-wave-particle-duality.mdx
   - 02-superposition-and-acoustics.mdx
   - 03-heisenberg-uncertainty.mdx
   - 04-entanglement-and-conservation.mdx
4. **Module 4: The Network of Fields** (`docs/04-StandardModel/`)
   - 01-space-occupiers-vs-messengers.mdx (Fermions vs Bosons)
   - 02-bound-fractional-chargers.mdx (Quarks)
   - 03-independent-integral-chargers.mdx (Leptons)
   - 04-identity-shifting-interaction.mdx (Weak Force)
   - 05-inertial-drag-field.mdx (Higgs Mechanism)

---

## 5. Agentic AI Pipeline Integration

Because Docusaurus is entirely file-based, the AI pipeline operates flawlessly:

1. **Initialization:** The Human Educator provides an outline for `docs/03-Quantum/02-superposition.mdx`.
2. **Writer Agent:** Drafts the `.mdx` file, importing the `<Term />` component and writing the acoustic analogies.
3. **Linter/Evaluator Agent:** Reads the saved `.mdx` file. It runs a regex check (e.g., `grep -i "fermion"`) to ensure the Writer didn't use forbidden jargon outside of a `<Term />` component.
4. **Reflection Loop:** If the Evaluator finds "spooky action at a distance", it rejects the draft, appending an error to the Agent Task file, forcing the Writer Agent to rewrite the file.
5. **Build Check:** A local CI script runs `npm run build` to ensure the MDX syntax is valid.

---

## 6. Deployment
Docusaurus builds to static HTML/JS/CSS. The site can be hosted for free using **GitHub Pages**, **Vercel**, or **Netlify**, with automated deployments triggered every time a new lesson passes the Evaluator Agent and is merged into the `main` branch.
