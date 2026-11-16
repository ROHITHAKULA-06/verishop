import React, { useState } from 'react';
import {
  ShieldX,
  AlertTriangle,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  AlertOctagon,
  Ban,
} from 'lucide-react';
import TrustGauge from './TrustGauge.jsx';
import TrustBreakdown from './TrustBreakdown.jsx';

/**
 * Extract clean domain name
 */
function cleanDomain(sourceName = '', url = '') {
  if (sourceName && !sourceName.startsWith('http')) {
    return sourceName.replace(/^www\./i, '');
  }
  try {
    const parsed = new URL(url.startsWith('http') ? url : `https://${url}`);
    return parsed.hostname.replace(/^www\./i, '');
  } catch {
    return sourceName || 'Unknown Site';
  }
}

/**
 * Format currency into INR style
 */
function formatPrice(price, currency = 'INR') {
  if (price === undefined || price === null || isNaN(Number(price))) {
    return null;
  }
  try {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: currency || 'INR',
      maximumFractionDigits: 0,
    }).format(Number(price));
  } catch {
    return `₹${Number(price).toLocaleString('en-IN')}`;
  }
}

/**
 * DiscardedCard component for Untrusted or High-Risk products
 *
 * @param {Object} props
 * @param {Object} props.item - RankedProduct object
 */
export default function DiscardedCard({ item }) {
  const [isExpanded, setIsExpanded] = useState(false);

  const product = item?.product || {};
  const trustScore = item?.trust_score || {};
  const source = product.source || {};
  const pricing = product.pricing || {};

  const domain = cleanDomain(source.source_name, source.source_url);
  const targetUrl = source.source_url || '#';
  const overallScore = Number(trustScore.overall_score || 0);
  const isUntrusted = (trustScore.verdict || '').toUpperCase() === 'UNTRUSTED';

  // Determine reason for discard
  const discardReason =
    item?.explanation ||
    trustScore?.explanation ||
    (trustScore?.risk_flags && trustScore.risk_flags.length > 0
      ? trustScore.risk_flags[0]
      : 'Trust score below verification threshold (< 50%). High risk of fraud, scam, or counterfeit goods.');

  const formattedPrice = formatPrice(pricing.price, pricing.currency);

  return (
    <div className="rounded-xl bg-red-950/20 border border-red-900/50 hover:border-red-600/60 shadow-lg shadow-black/40 transition-all duration-200 overflow-hidden">
      {/* Top Warning Banner */}
      <div className="px-5 py-2 bg-red-950/60 border-b border-red-900/60 flex items-center justify-between text-xs text-red-300">
        <div className="flex items-center space-x-2 font-semibold">
          <Ban className="w-4 h-4 text-red-400" />
          <span className="uppercase tracking-wider">
            {isUntrusted ? 'Untrusted Listing' : 'Below Selected Trust Threshold'}
          </span>
        </div>
        <span className="text-[11px] text-red-400 font-mono">
          {isUntrusted ? 'High-Risk Verdict' : 'Selected Minimum Not Met'}
        </span>
      </div>

      {/* Main Content */}
      <div className="p-5 md:p-6 flex flex-col md:flex-row gap-5 items-start">
        {/* Discarded Icon / Gauge */}
        <div className="flex md:flex-col items-center justify-between md:justify-center p-3 rounded-lg bg-slate-950/80 border border-red-900/40 flex-shrink-0 w-full md:w-28 gap-2">
          <TrustGauge score={overallScore} size="sm" showLabel={false} />
          <div className="text-center">
            <span className="text-[10px] uppercase font-bold text-red-400 block tracking-wider">
              {isUntrusted ? 'High Risk' : 'Caution'}
            </span>
            <span className="text-[9px] text-slate-500 font-mono">
              Score: {Math.round(overallScore * 100)}%
            </span>
          </div>
        </div>

        {/* Info Column */}
        <div className="flex-1 min-w-0">
          <div className="flex flex-wrap items-center gap-2 mb-2">
            <span className="px-2.5 py-0.5 rounded bg-slate-900 border border-slate-700 text-xs font-mono text-slate-300">
              {domain}
            </span>

            {product.seller_name && (
              <span className="text-xs text-slate-400">
                Seller: <strong className="text-slate-300">{product.seller_name}</strong>
              </span>
            )}

            {formattedPrice && (
              <span className="text-xs text-amber-400/90 font-mono bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20">
                Advertised: {formattedPrice}
              </span>
            )}
          </div>

          {/* Product Title */}
          <h4 className="text-base font-semibold text-slate-200 mb-2">
            {product.title || 'Unknown Product Listing'}
          </h4>

          {/* Discard Reason Callout */}
          <div className="p-3 rounded-lg bg-red-950/40 border border-red-500/30 text-xs text-red-200 mb-3">
            <div className="flex items-start space-x-2">
              <AlertOctagon className="w-4 h-4 text-red-400 mt-0.5 flex-shrink-0" />
              <div>
                <strong className="font-semibold text-red-300 block mb-0.5">
                  Reason for Discard:
                </strong>
                <p className="text-red-200/90 leading-relaxed">{discardReason}</p>
              </div>
            </div>
          </div>

          {/* Risk Flags quick list */}
          {trustScore?.risk_flags && trustScore.risk_flags.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mb-2">
              {trustScore.risk_flags.map((flag, idx) => (
                <span
                  key={idx}
                  className="inline-flex items-center space-x-1 px-2 py-0.5 rounded bg-red-900/30 border border-red-700/40 text-[11px] text-red-300"
                >
                  <AlertTriangle className="w-3 h-3 text-red-400" />
                  <span>{flag}</span>
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Expandable Footer */}
      <div className="px-5 py-2.5 bg-slate-950/60 border-t border-red-900/40 flex items-center justify-between text-xs text-slate-400">
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="inline-flex items-center space-x-1.5 font-medium text-red-400 hover:text-red-300 transition-colors focus:outline-none"
        >
          <span>{isExpanded ? 'Hide Trust Factor Analysis' : 'Inspect Score and Risk Factors'}</span>
          {isExpanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>

        {targetUrl !== '#' && (
          <a
            href={targetUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center space-x-1 text-slate-500 hover:text-red-400 transition-colors"
            title="Warning: Visiting untrusted sites may expose you to phishing or malvertising"
          >
            <span className="text-[11px]">Inspect Source (Cautiously)</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        )}
      </div>

      {/* Collapsed Trust Breakdown */}
      {isExpanded && (
        <div className="px-5 pb-5 pt-1 bg-slate-950/80 border-t border-red-900/40">
          <TrustBreakdown trustScore={trustScore} />
        </div>
      )}
    </div>
  );
}
