import React from 'react';
import {
  ShieldCheck,
  ShieldAlert,
  Lock,
  Globe,
  MessageSquare,
  Award,
  AlertTriangle,
  Info,
  CheckCircle2,
  XCircle,
} from 'lucide-react';

/**
 * Returns an appropriate icon based on the factor name
 */
function getFactorIcon(name = '') {
  const lower = name.toLowerCase();
  if (lower.includes('ssl') || lower.includes('security') || lower.includes('connection')) {
    return <Lock className="w-4 h-4 text-sky-400" />;
  }
  if (lower.includes('domain') || lower.includes('whois') || lower.includes('dns') || lower.includes('host')) {
    return <Globe className="w-4 h-4 text-indigo-400" />;
  }
  if (lower.includes('reddit') || lower.includes('review') || lower.includes('sentiment') || lower.includes('community')) {
    return <MessageSquare className="w-4 h-4 text-orange-400" />;
  }
  if (lower.includes('seller') || lower.includes('credibility') || lower.includes('brand') || lower.includes('warranty')) {
    return <Award className="w-4 h-4 text-emerald-400" />;
  }
  return <ShieldCheck className="w-4 h-4 text-blue-400" />;
}

/**
 * Comprehensive Trust Breakdown component
 * Displays factors, evidence lists, risk flags, and confidence rating.
 *
 * @param {Object} props
 * @param {Object} props.trustScore - TrustScore object
 * @param {string} [props.className='']
 */
export default function TrustBreakdown({ trustScore, className = '' }) {
  if (!trustScore) {
    return null;
  }

  const {
    overall_score = 0,
    verdict = 'UNKNOWN',
    factors = [],
    risk_flags = [],
    confidence = 0.5,
    explanation = '',
  } = trustScore;

  const confidencePct = Math.round((Number(confidence) || 0) * 100);

  return (
    <div className={`space-y-4 pt-3 border-t border-slate-800/80 text-sm ${className}`}>
      {/* Header bar: Confidence & verdict quick info */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-1">
        <div className="flex items-center space-x-2">
          <span className="text-xs uppercase font-semibold tracking-wider text-slate-400">
            Trust Breakdown & Verification Trail
          </span>
        </div>
        <div className="flex items-center space-x-2 text-xs">
          <span className="text-slate-400">Confidence:</span>
          <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-200 font-mono font-medium border border-slate-700">
            {confidencePct}%
          </span>
        </div>
      </div>

      {/* Explanation text */}
      {explanation && (
        <div className="p-3 rounded-lg bg-slate-900/90 border border-slate-800 text-slate-300 text-xs leading-relaxed flex items-start space-x-2.5">
          <Info className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
          <p>{explanation}</p>
        </div>
      )}

      {/* Risk Flags Callout if any */}
      {risk_flags && risk_flags.length > 0 && (
        <div className="p-3 rounded-lg bg-red-950/40 border border-red-500/40 text-red-200">
          <div className="flex items-center space-x-2 mb-2 font-semibold text-xs text-red-400 uppercase tracking-wider">
            <ShieldAlert className="w-4 h-4 text-red-400" />
            <span>Risk Flags Detected ({risk_flags.length})</span>
          </div>
          <ul className="space-y-1.5 text-xs text-red-300/90">
            {risk_flags.map((flag, idx) => (
              <li key={idx} className="flex items-start space-x-2">
                <AlertTriangle className="w-3.5 h-3.5 text-red-400 mt-0.5 flex-shrink-0" />
                <span>{flag}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Factors list */}
      <div className="space-y-3.5">
        {factors.map((factor, idx) => {
          const name = factor.factor_name || factor.name || `Factor #${idx + 1}`;
          const factorScore = Number(factor.score) || 0;
          const factorPct = Math.round(factorScore > 1 ? factorScore : factorScore * 100);
          const weightPct = factor.weight ? Math.round(Number(factor.weight) * 100) : null;

          // Color calculation
          let barBg = 'bg-emerald-500';
          let textColor = 'text-emerald-400';
          let badgeBorder = 'border-emerald-500/30 bg-emerald-500/10';

          if (factorPct < 50) {
            barBg = 'bg-red-500';
            textColor = 'text-red-400';
            badgeBorder = 'border-red-500/30 bg-red-500/10';
          } else if (factorPct < 70) {
            barBg = 'bg-amber-500';
            textColor = 'text-amber-400';
            badgeBorder = 'border-amber-500/30 bg-amber-500/10';
          }

          const evidenceList = Array.isArray(factor.evidence) ? factor.evidence : [];

          return (
            <div
              key={idx}
              className="p-3 rounded-lg bg-slate-900/60 border border-slate-800/80 hover:border-slate-700/80 transition-colors"
            >
              {/* Factor header */}
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2 min-w-0">
                  <div className="p-1 rounded bg-slate-800 border border-slate-700">
                    {getFactorIcon(name)}
                  </div>
                  <span className="font-medium text-slate-200 text-xs md:text-sm truncate">
                    {name}
                  </span>
                  {weightPct !== null && (
                    <span className="text-[10px] text-slate-400 px-1.5 py-0.5 rounded bg-slate-800/80 font-mono">
                      wt: {weightPct}%
                    </span>
                  )}
                </div>

                <div className={`px-2 py-0.5 rounded text-xs font-mono font-bold border ${badgeBorder} ${textColor}`}>
                  {factorPct}%
                </div>
              </div>

              {/* Progress bar */}
              <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden mb-2.5">
                <div
                  className={`h-full ${barBg} rounded-full transition-all duration-700 ease-out`}
                  style={{ width: `${factorPct}%` }}
                />
              </div>

              {/* Evidence bullets */}
              {evidenceList.length > 0 && (
                <div className="mt-2 pl-1 space-y-1">
                  {evidenceList.map((item, eIdx) => (
                    <div key={eIdx} className="flex items-start space-x-2 text-xs text-slate-400">
                      <span className="text-slate-600 mt-1 select-none">•</span>
                      <span className="leading-relaxed">{item}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
