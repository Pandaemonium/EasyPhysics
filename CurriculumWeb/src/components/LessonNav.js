import React from 'react';
import Link from '@docusaurus/Link';

export default function LessonNav({
  nextLabel,
  nextTo,
  mathLabel,
  mathTo,
  note,
}) {
  return (
    <nav className="lesson-nav" aria-label="Lesson choices">
      {note ? <p className="lesson-nav__note">{note}</p> : null}
      <div className="lesson-nav__actions">
        {nextTo ? (
          <Link className="lesson-nav__button lesson-nav__button--primary" to={nextTo}>
            Continue: {nextLabel}
          </Link>
        ) : null}
        {mathTo ? (
          <Link className="lesson-nav__button lesson-nav__button--secondary" to={mathTo}>
            Optional Math Lens: {mathLabel}
          </Link>
        ) : null}
      </div>
    </nav>
  );
}
