import React, {useId, useState} from 'react';

export default function KnowledgeCheck({
  title = 'Knowledge check',
  question,
  options,
}) {
  const [selectedIndex, setSelectedIndex] = useState(null);
  const checkId = useId();
  const selected = selectedIndex === null ? null : options[selectedIndex];

  return (
    <section className="knowledge-check" aria-labelledby={`${checkId}-title`}>
      <div className="knowledge-check__eyebrow" id={`${checkId}-title`}>
        {title}
      </div>
      <p className="knowledge-check__question">{question}</p>
      <div className="knowledge-check__options" role="list">
        {options.map((option, index) => {
          const isSelected = selectedIndex === index;
          const resultClass =
            isSelected && option.correct
              ? 'knowledge-check__option--correct'
              : isSelected
                ? 'knowledge-check__option--incorrect'
                : '';

          return (
            <button
              type="button"
              className={`knowledge-check__option ${resultClass}`}
              aria-pressed={isSelected}
              onClick={() => setSelectedIndex(index)}
              key={`${option.label}-${option.text}`}>
              <span className="knowledge-check__label">{option.label}</span>
              <span>{option.text}</span>
            </button>
          );
        })}
      </div>
      {selected ? (
        <p
          className={`knowledge-check__feedback ${
            selected.correct
              ? 'knowledge-check__feedback--correct'
              : 'knowledge-check__feedback--incorrect'
          }`}
          role="status">
          <strong>{selected.correct ? 'Yes.' : 'Not quite.'}</strong>{' '}
          {selected.feedback}
        </p>
      ) : null}
    </section>
  );
}
