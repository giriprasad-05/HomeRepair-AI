import React from 'react';
import './StatusBadge.css';

export function StatusBadge({ type = 'status', value, label }) {
  if (!value) return null;

  const normalized = String(value).toLowerCase().replace(/\s+/g, '_');
  const displayLabel = label || value.replace(/_/g, ' ');

  let className = 'status-badge';
  if (type === 'severity') {
    className += ` severity-${normalized}`;
  } else if (type === 'warranty') {
    className += ` warranty-${normalized}`;
  } else {
    className += ` status-${normalized}`;
  }

  const showDot = type === 'status';

  return (
    <span className={className}>
      {showDot && <span className="status-badge-dot" />}
      {displayLabel}
    </span>
  );
}

export default StatusBadge;
