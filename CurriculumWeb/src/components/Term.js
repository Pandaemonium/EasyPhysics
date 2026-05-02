import React from 'react';

export default function Term({ intuitive, jargon, definition }) {
  return (
    <span 
      className="glossary-term" 
      tabIndex="0" 
      title={`${jargon}: ${definition}`}
      style={{ borderBottom: '1px dashed currentColor', cursor: 'help' }}>
      {intuitive}
    </span>
  );
}