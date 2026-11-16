import React from 'react';

/**
 * Circular progress gauge displaying Trust Score
 * Color-coded: green >=70%, yellow 50-70%, red <50%
 *
 * @param {Object} props
 * @param {number} props.score - Trust score between 0.0 and 1.0 (or 0-100)
 * @param {'sm' | 'md' | 'lg'} [props.size='md'] - Display size
 * @param {boolean} [props.showLabel=true] - Show text label under percentage
 * @param {string} [props.className=''] - Additional CSS classes
 */
export default function TrustGauge({
  score = 0,
  size = 'md',
  showLabel = false,
  className = '',
}) {
  // Normalize score to 0 - 100 percentage
  const numScore = Number(score) || 0;
  const pct = Math.min(100, Math.max(0, Math.round(numScore > 1 ? numScore : numScore * 100)));

  // Determine color scheme
  let strokeColor = '#10B981'; // green (>= 70%)
  let textColor = 'text-emerald-400';
  let glowColor = 'rgba(16, 185, 129, 0.2)';

  if (pct < 50) {
    strokeColor = '#EF4444'; // red (< 50%)
    textColor = 'text-red-400';
    glowColor = 'rgba(239, 68, 68, 0.2)';
  } else if (pct < 70) {
    strokeColor = '#F59E0B'; // yellow (50-70%)
    textColor = 'text-amber-400';
    glowColor = 'rgba(245, 158, 11, 0.2)';
  }

  // Dimensions based on size
  const config = {
    sm: { size: 52, strokeWidth: 4.5, textClass: 'text-xs font-bold', labelClass: 'text-[9px]' },
    md: { size: 84, strokeWidth: 6.5, textClass: 'text-lg font-black', labelClass: 'text-[10px]' },
    lg: { size: 116, strokeWidth: 8.5, textClass: 'text-2xl font-black', labelClass: 'text-xs' },
  }[size] || { size: 84, strokeWidth: 6.5, textClass: 'text-lg font-black', labelClass: 'text-[10px]' };

  const center = config.size / 2;
  const radius = center - config.strokeWidth;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (pct / 100) * circumference;

  return (
    <div className={`relative inline-flex flex-col items-center justify-center ${className}`}>
      <div className="relative flex items-center justify-center" style={{ width: config.size, height: config.size }}>
        <svg
          width={config.size}
          height={config.size}
          className="transform -rotate-90"
          style={{ filter: `drop-shadow(0 0 6px ${glowColor})` }}
        >
          {/* Background circle track */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="transparent"
            stroke="#1F2937"
            strokeWidth={config.strokeWidth}
          />
          {/* Progress circle */}
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="transparent"
            stroke={strokeColor}
            strokeWidth={config.strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            style={{
              transition: 'stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1)',
            }}
          />
        </svg>

        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
          <span className={`font-mono tracking-tight leading-none ${textColor} ${config.textClass}`}>
            {pct}%
          </span>
          {showLabel && size !== 'sm' && (
            <span className={`text-slate-400 uppercase tracking-widest font-semibold mt-0.5 ${config.labelClass}`}>
              Trust
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
