# Docusaurus Architecture Plan: EasyPhysics Curriculum

## 1. Why Docusaurus?

Docusaurus is a good fit for EasyPhysics because it keeps the curriculum in plain text while still allowing interactive teaching tools.

1. **MDX support:** Lessons can stay readable as Markdown while embedding React components for glossary terms, diagrams, checks, and optional simulations.
2. **Git-native workflow:** Drafts, reviews, glossary files, and published lessons can all be inspected, diffed, tested, and versioned.
3. **Explicit navigation:** `sidebars.js` can enforce the concept-first learning path instead of leaving learners in an unordered page pile.
4. **Static deployment:** The site can build to static HTML, CSS, and JavaScript while still supporting interactive client-side learning components.

## 2. Current Repository Structure

The Docusaurus app lives under `CurriculumWeb/`. Generated article artifacts stay separate from publishable docs until a promotion step copies or converts them.

```text
C:\Projects\EasyPhysics\
|-- AgentTasks/
|   |-- generated_articles/          # Automated article workflow outputs
|   |-- article_workflow_globals/    # Shared generated artifacts
|   `-- logs/                        # Agent and workflow logs
|-- CurriculumWeb/                   # Docusaurus app
|   |-- docs/
|   |   |-- intro.mdx                # Start Here entry page
|   |   |-- wiki/                    # Core concept lessons and draft doorways
|   |   `-- math/                    # Optional Math Lens pages
|   |-- src/
|   |   |-- components/
|   |   |   |-- Term.js              # Glossary tooltip component
|   |   |   |-- KnowledgeCheck.js    # Interactive lesson checks
|   |   |   |-- LessonNav.js         # Continue / optional math choices
|   |   |   `-- ConceptFlow.js       # Compact concept-path visual
|   |   |-- css/
|   |   |   `-- custom.css           # Site, glossary, and lesson component styling
|   |   `-- data/
|   |       `-- glossary.json        # Data-driven glossary entries
|   |-- static/                      # Static assets
|   |-- docusaurus.config.js
|   `-- sidebars.js
|-- auto_generate_articles.py        # Local LLM drafting and review pipeline
`-- AGENTS.md                        # Shared repo guidance for agents
```

## 3. Current MVP Content Architecture

The first prototype focuses on a single short learning path:

```text
state -> change -> symmetry -> conservation
```

The point of the MVP is to prove the lesson format, optional math detours, glossary behavior, knowledge checks, and sidebar flow before building the larger physics wiki.

Current public navigation in `CurriculumWeb/sidebars.js`:

```text
Start Here
MVP Path: State, Change, Symmetry
  What Physics Looks For
  What Is a State?
  Change Rules
  Symmetry
  Conservation
  Energy
  Where This Leads
Optional Math Lens
  Coordinates
  Functions as Rules
  Tiny Noether Preview
Draft Doorways
  Discrete vs. Continuous Symmetries
  The Speed of Causality
  Geodesics and Gravity
  Wave-Particle Duality
  Superposition and Acoustics
  Space-Occupiers vs. Messengers
```

Current MVP lesson files:

```text
CurriculumWeb/docs/wiki/00-what-is-physics-looking-for.mdx
CurriculumWeb/docs/wiki/01-what-is-a-state.mdx
CurriculumWeb/docs/wiki/02-change-rules.mdx
CurriculumWeb/docs/wiki/03-symmetry-change-that-does-not-matter.mdx
CurriculumWeb/docs/wiki/04-conservation-memory-of-symmetry.mdx
CurriculumWeb/docs/wiki/05-energy-time-sameness.mdx
CurriculumWeb/docs/wiki/06-where-this-path-leads.mdx
```

Current optional math files:

```text
CurriculumWeb/docs/math/coordinates.mdx
CurriculumWeb/docs/math/functions-as-rules.mdx
CurriculumWeb/docs/math/tiny-noether-preview.mdx
```

## 4. Lesson Structure Philosophy

Lessons should be consistent for learners, but not formulaic in prose. The shared contract is:

```text
Every lesson needs a clear learner outcome, a short knowledge check, and a next step.
Everything else should fit the concept being taught.
```

Authors can choose from reusable lesson moves:

```text
Hook question
Tiny scenario
Core idea
Picture or diagram
Contrast two mental models
Misconception trap
Standard term reveal
One-sentence recap
Knowledge check
Math detour
Next door
```

Required pieces for promoted lessons:

- Frontmatter with `title`, `slug`, `sidebar_label`, `description`, `prerequisites`, `glossary_terms`, and `status`.
- A short body focused on one load-bearing idea.
- One or two `KnowledgeCheck` questions.
- A `LessonNav` next step.
- An optional Math Lens link when the math would sharpen the idea.

Recommended future frontmatter additions:

```yaml
learning_goal: "Explain symmetry as a change that leaves the rulebook unchanged."
estimated_time: "5-8 minutes"
reader_level: "motivated beginner"
math_lens:
  - /docs/math/tiny-noether-preview
```

## 5. Optional Math Lens Pattern

Math pages are optional depth, not a second-class route and not a barrier to the main path.

The core flow should feel like:

```text
Core lesson -> concept check -> next lesson
             -> optional Math Lens -> math check -> rejoin path
```

A Math Lens page should usually answer:

1. What problem this math solves.
2. The smallest useful symbol or equation.
3. What each symbol is doing.
4. A tiny example or interpretation.
5. A short knowledge check.
6. A return link to the relevant core lesson.

The main lesson should remain understandable without the Math Lens.

## 6. Teaching Components

The current reusable MDX components are:

### `Term`

`Term` wraps standard terminology in a data-driven glossary tooltip. It supports mouse hover, keyboard focus, and tap/click. MDX should prefer glossary keys over repeated inline definitions.

```mdx
import Term from '@site/src/components/Term';

A <Term name="symmetry">symmetry</Term> is a change that leaves the rulebook unchanged.
```

Glossary data lives in `CurriculumWeb/src/data/glossary.json`:

```json
{
  "symmetry": {
    "standard": "symmetry",
    "intuitive": "change that does not matter",
    "definition": "A change in setup or description that leaves the relevant rule unchanged."
  }
}
```

The older prop-based form remains supported for older generated pages:

```mdx
<Term
  intuitive="space-occupier"
  jargon="fermion"
  definition="A particle type that obeys the Pauli exclusion principle."
/>
```

### `KnowledgeCheck`

`KnowledgeCheck` gives a short interactive multiple-choice check with feedback for each option.

Knowledge checks should test understanding rather than vocabulary. A good wrong answer should correspond to a common misconception.

### `LessonNav`

`LessonNav` presents the learner with the next core lesson and, when relevant, an optional Math Lens.

### `ConceptFlow`

`ConceptFlow` displays the project spine, such as `state -> change -> symmetry -> conservation`, and can highlight the current concept.

## 7. Frontmatter and Status

Each Docusaurus page should include frontmatter like:

```yaml
---
title: "Symmetry: A Change That Does Not Matter"
slug: /wiki/symmetry-change-that-does-not-matter
sidebar_label: "Symmetry"
description: "A short lesson on symmetry as a change that leaves the rulebook unchanged."
prerequisites:
  - change-rules
glossary_terms:
  - symmetry
  - continuous-symmetry
  - change-rule
status: draft
---
```

Use `status: draft | reviewed | published` to distinguish Docusaurus-visible content from human-approved content. The site can build with draft pages, but the promotion workflow should know which pages are ready.

## 8. Promotion Workflow

The automated drafting system should not write directly into published curriculum docs by default.

Recommended flow:

```text
AgentTasks/generated_articles/<slug>/final.mdx
  -> automated claim/source/review pass
  -> promotion script validates frontmatter and glossary terms
  -> human editor approves
  -> CurriculumWeb/docs/wiki/<slug>.mdx or CurriculumWeb/docs/math/<slug>.mdx
  -> npm run build
```

Promotion checks should include:

- MDX parses successfully.
- Required frontmatter is present.
- Referenced glossary term keys exist.
- Knowledge checks have exactly one correct answer unless intentionally marked otherwise.
- Optional Math Lens links resolve.
- Unsupported or unresolved claim checks do not pass promotion.
- No obvious mojibake patterns appear in the output.
- Generated text avoids unintended smart punctuation.
- The page appears in `sidebars.js` or an intentional generated sidebar.

## 9. Linting and Evaluation

Avoid simple regex-only jargon checks. A useful checker should ignore frontmatter, imports, code fences, and JSX props before flagging unwrapped standard terms.

Suggested checks:

- `npm run build` for MDX and Docusaurus validation.
- A glossary checker for `<Term name="...">` keys.
- A frontmatter checker for `title`, `slug`, `description`, `prerequisites`, `glossary_terms`, and `status`.
- A knowledge-check checker for malformed options and missing feedback.
- A link checker for lesson and Math Lens routes.
- A claim gate that requires all extracted claims to pass before promotion.
- A text hygiene checker for mojibake and unintended smart punctuation.

## 10. Accessibility Requirements

The project needs both conceptual accessibility and web accessibility.

Current and future components should support:

- Keyboard navigation.
- Visible focus states.
- Touch/click behavior, not hover-only interaction.
- Semantic headings and landmarks.
- Sufficient contrast in light and dark modes.
- Reduced-motion-friendly animations when animations are added.
- Alt text or text equivalents for diagrams.
- Math explanations in words before or beside symbols.

Tooltips should never be the only place where essential information appears. They reduce friction, but the core lesson should still make sense when read linearly.

## 11. Build and Preview

Primary verification command:

```bash
npm run build
```

Local preview options from `CurriculumWeb/`:

```bash
npm run start
npm run serve
```

After a production build, `npm run serve` previews the static output. The current MVP has been verified with `npm run build`, and the prototype can be previewed locally from the first lesson route:

```text
http://127.0.0.1:3001/docs/wiki/what-is-physics-looking-for
```

The port may differ depending on what is already running.

## 12. Deployment

Docusaurus builds to static HTML, JavaScript, and CSS. GitHub Pages, Vercel, and Netlify are all viable. Before public deployment, set the real site `url`, optional `baseUrl`, repository links, and social preview image in `CurriculumWeb/docusaurus.config.js`.

Until those values are known, keep template Docusaurus links out of the public navigation.
