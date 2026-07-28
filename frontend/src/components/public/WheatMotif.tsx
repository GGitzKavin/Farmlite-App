import React from 'react';

/**
 * A single hand-drawn-style wheat sprig, used as FarmLite's recurring
 * signature motif across the public marketing pages (hero, section
 * dividers, footer). Deliberately linework-only so it reads as an
 * illustrated mark rather than a stock icon.
 */
const WheatMotif: React.FC<{ className?: string; color?: string }> = ({
  className = 'h-16 w-16',
  color = '#606c38',
}) => (
  <svg
    viewBox="0 0 64 120"
    className={className}
    fill="none"
    stroke={color}
    strokeWidth="2.25"
    strokeLinecap="round"
    aria-hidden="true"
  >
    <path d="M32 8 V112" />
    {[18, 32, 46, 60, 74].map((y, i) => (
      <g key={y}>
        <path d={`M32 ${y} C 20 ${y - 10}, 14 ${y - 4}, 10 ${y + 6} C 18 ${y + 4}, 26 ${y + 6}, 32 ${y + 12}`} />
        <path d={`M32 ${y} C 44 ${y - 10}, 50 ${y - 4}, 54 ${y + 6} C 46 ${y + 4}, 38 ${y + 6}, 32 ${y + 12}`} />
        {i < 4 && <ellipse cx={32} cy={y - 6} rx="3.2" ry="6" transform={`rotate(0 32 ${y - 6})`} />}
      </g>
    ))}
    <ellipse cx="32" cy="10" rx="3.4" ry="7" />
  </svg>
);

export default WheatMotif;
