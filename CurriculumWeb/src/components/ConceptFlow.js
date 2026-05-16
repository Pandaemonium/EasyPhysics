import React from 'react';

const defaultSteps = [
  'state',
  'change',
  'symmetry',
  'conservation',
  'field',
  'particle',
  'interaction',
  'geometry',
];

export default function ConceptFlow({steps = defaultSteps, current}) {
  return (
    <ol className="concept-flow" aria-label="Concept path">
      {steps.map((step) => (
        <li
          className={`concept-flow__step ${
            current === step ? 'concept-flow__step--current' : ''
          }`}
          key={step}>
          {step}
        </li>
      ))}
    </ol>
  );
}
