import React from 'react';
import {
  ShieldCheck,
  Ban,
  Clock,
  Sparkles,
  ExternalLink,
  Award,
  Globe,
  ArrowUpRight,
} from 'lucide-react';
import TrustGauge from './TrustGauge.jsx';

/**
 * Format currency into INR style
 */
function formatPrice(price, currency = 'INR') {
  if (price === undefined || price === null || isNaN(Number(price))) {
    return '';
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
 * Summary Section displaying high-level verification metrics and top recommendation
 *
 * @param {Object} props
 * @param {Array} props.trustedResults - Array of trusted RankedProduct objects
 * @param {Array} props.discardedResults - Array of discarded RankedProduct objects
 * @param {number} props.processingTimeMs - Execution duration in ms
 * @param {RankedProduct} [props.bestRecommendation] - Top-ranked product
 */
export default function Summary({
  trustedResults = [],
  discardedResults = [],
  processingTimeMs = 0,
  bestRecommendation = null,
}) {
  const totalAnalyzed = trustedResults.length + discardedResults.length;
  const timeInSeconds = (processingTimeMs / 1000).toFixed(2);

  // Compute average trust score across all results
  const allResults = [...trustedResults, ...discardedResults];
  const avgTrustScore =
    allResults.length > 0
      ? Math.round(
          (allResults.reduce(
            (sum, item) => sum + Number(item?.trust_score?.overall_score || 0),
            0
          ) /
            allResults.length) *
            100
        )
      : 0;

  const topProduct = bestRecommendation || trustedResults[0];
  const topProductPricing = topProduct?.product?.pricing;
  const topProductSource = topProduct?.product?.source;

  return (
    <div className="mt-12 pt-8 border-t border-slate-800">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="text-lg font-bold text-slate-100 flex items-center space-x-2">
            <Sparkles className="w-5 h-5 text-emerald-400" />
            <span>Verification Pipeline Summary</span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Overview of multi-source trust scoring and safety analysis
          </p>
        </div>
      </div>

      {/* Grid of Key Metrics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3.5 mb-6">
        {/* Total Analyzed */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs uppercase font-medium tracking-wider">Websites Analyzed</span>
            <Globe className="w-4 h-4 text-blue-400" />
          </div>
          <div className="text-2xl font-black font-mono text-slate-100">
            {totalAnalyzed}
          </div>
          <span className="text-[11px] text-slate-500 mt-1">Cross-platform sweep</span>
        </div>

        {/* Trusted Count */}
        <div className="p-4 rounded-xl bg-emerald-950/20 border border-emerald-500/30 flex flex-col justify-between">
          <div className="flex items-center justify-between text-emerald-400 mb-2">
            <span className="text-xs uppercase font-medium tracking-wider">Trusted Listings</span>
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-black font-mono text-emerald-400">
            {trustedResults.length}
          </div>
          <span className="text-[11px] text-emerald-400/70 mt-1">Passed all safety criteria</span>
        </div>

        {/* Discarded Count */}
        <div className="p-4 rounded-xl bg-red-950/20 border border-red-500/30 flex flex-col justify-between">
          <div className="flex items-center justify-between text-red-400 mb-2">
            <span className="text-xs uppercase font-medium tracking-wider">Discarded / Risky</span>
            <Ban className="w-4 h-4 text-red-400" />
          </div>
          <div className="text-2xl font-black font-mono text-red-400">
            {discardedResults.length}
          </div>
          <span className="text-[11px] text-red-400/70 mt-1">Failed trust thresholds</span>
        </div>

        {/* Processing Time */}
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 flex flex-col justify-between">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs uppercase font-medium tracking-wider">Processing Time</span>
            <Clock className="w-4 h-4 text-purple-400" />
          </div>
          <div className="text-2xl font-black font-mono text-slate-100">
            {timeInSeconds}s
          </div>
          <span className="text-[11px] text-slate-500 mt-1">
            Avg Trust: <strong className="text-slate-300">{avgTrustScore}%</strong>
          </span>
        </div>
      </div>

      {/* Best Recommendation Highlight Banner */}
      {topProduct && (
        <div className="p-5 md:p-6 rounded-2xl bg-gradient-to-r from-emerald-950/50 via-slate-900 to-slate-900 border border-emerald-500/40 shadow-xl shadow-emerald-950/30">
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="flex items-start space-x-4">
              <div className="p-3 rounded-xl bg-emerald-500/20 border border-emerald-500/30 text-emerald-400 flex-shrink-0">
                <Award className="w-6 h-6" />
              </div>

              <div>
                <div className="flex items-center space-x-2 mb-1">
                  <span className="px-2 py-0.5 rounded-full bg-emerald-500/20 border border-emerald-500/40 text-[11px] font-bold text-emerald-300 uppercase tracking-wider">
                    ★ Best Recommendation
                  </span>
                  <span className="text-xs font-mono text-slate-400">
                    via {topProductSource?.source_name || 'Verified Source'}
                  </span>
                </div>

                <h4 className="text-base md:text-lg font-bold text-slate-100 line-clamp-1">
                  {topProduct.product?.title}
                </h4>

                <p className="text-xs text-slate-400 mt-1 line-clamp-1">
                  {topProduct.explanation || 'Optimal combination of verified domain security, community reputation, and pricing.'}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-4 self-end md:self-auto flex-shrink-0">
              {topProductPricing?.price && (
                <div className="text-right">
                  <span className="text-xs text-slate-400 block">Verified Price</span>
                  <span className="text-xl font-mono font-black text-emerald-400">
                    {formatPrice(topProductPricing.price, topProductPricing.currency)}
                  </span>
                </div>
              )}

              {topProductSource?.source_url && (
                <a
                  href={topProductSource.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="px-4 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs inline-flex items-center space-x-1.5 shadow-md shadow-emerald-500/20 transition-colors"
                >
                  <span>Go to Store</span>
                  <ArrowUpRight className="w-4 h-4" />
                </a>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
