import React, {useId, useState} from 'react';
import glossary from '@site/src/data/glossary.json';

export default function Term({
  name,
  intuitive,
  jargon,
  definition,
  children,
}) {
  const [open, setOpen] = useState(false);
  const tooltipId = useId();
  const entry = name ? glossary[name] : null;
  const label = children || intuitive || entry?.intuitive || entry?.standard || name;
  const standard = jargon || entry?.standard || name || label;
  const body = definition || entry?.definition || '';

  if (!body) {
    return <span className="glossary-term glossary-term--missing">{label}</span>;
  }

  return (
    <span
      className="glossary-term-wrap"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) {
          setOpen(false);
        }
      }}>
      <button
        type="button"
        className="glossary-term"
        aria-describedby={tooltipId}
        aria-expanded={open}
        onFocus={() => setOpen(true)}
        onClick={() => setOpen((value) => !value)}>
        {label}
      </button>
      <span
        id={tooltipId}
        role="tooltip"
        className="glossary-tooltip"
        hidden={!open}>
        <strong>{standard}</strong>: {body}
      </span>
    </span>
  );
}
