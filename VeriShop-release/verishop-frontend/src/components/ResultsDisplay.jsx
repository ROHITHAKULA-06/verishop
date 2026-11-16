import React, { useState, useMemo, useEffect } from 'react';
import {
  ShieldCheck,
  Ban,
  Clock,
  ArrowUpDown,
  Filter,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
} from 'lucide-react';
import ProductCard from './ProductCard.jsx';
import DiscardedCard from './DiscardedCard.jsx';
import Summary from './Summary.jsx';

/**
 * ResultsDisplay Component
 * Separates results into Trusted vs Discarded tabs and renders cards and summary.
 *
 * @param {Object} props
 * @param {Object} props.data - SearchResponse object
 * @param {string} props.query - Search query string
 */
export default function ResultsDisplay({ data, query }) {
  const [activeTab, setActiveTab] = useState('trusted'); // 'trusted' | 'discarded'
  const [sortBy, setSortBy] = useState('trust'); // 'trust' | 'blended' | 'price_asc' | 'price_desc'

  const results = Array.isArray(data?.results) ? data.results : [];
  const totalFound = data?.total_found ?? results.length;
  const processingTimeMs = data?.processing_time_ms ?? 0;
  const minimumTrust = Number(data?.metadata?.min_trust_score ?? 0.5);

  // Split results into Trusted vs Discarded
  // Only high-confidence trusted verdicts belong in Trusted. Caution and
  // untrusted listings are shown under Discarded so they remain inspectable.
  const { trustedResults, discardedResults } = useMemo(() => {
    const trusted = [];
    const discarded = [];

    results.forEach((item) => {
      const verdict = (item?.trust_score?.verdict || '').toUpperCase();
      const score = Number(item?.trust_score?.overall_score || 0);

      if (verdict !== 'UNTRUSTED' && score >= minimumTrust) {
        trusted.push(item);
      } else {
        discarded.push(item);
      }
    });

    return { trustedResults: trusted, discardedResults: discarded };
  }, [results, minimumTrust]);

  // After each search, open the tab that actually has results. In particular,
  // don't leave users staring at an empty Trusted tab when every listing needs
  // caution or is untrusted.
  useEffect(() => {
    if (trustedResults.length === 0 && discardedResults.length > 0) {
      setActiveTab('discarded');
    } else if (trustedResults.length > 0) {
      setActiveTab('trusted');
    }
  }, [data?.request_id, trustedResults.length, discardedResults.length]);

  // Sort active list based on user preference
  const sortedTrusted = useMemo(() => {
    const list = [...trustedResults];
    switch (sortBy) {
      case 'trust':
        return list.sort(
          (a, b) =>
            Number(b?.trust_score?.overall_score || 0) -
            Number(a?.trust_score?.overall_score || 0)
        );
      case 'price_asc':
        return list.sort(
          (a, b) =>
            Number(a?.product?.pricing?.price || 0) -
            Number(b?.product?.pricing?.price || 0)
        );
      case 'price_desc':
        return list.sort(
          (a, b) =>
            Number(b?.product?.pricing?.price || 0) -
            Number(a?.product?.pricing?.price || 0)
        );
      case 'blended':
      default:
        return list.sort(
          (a, b) =>
            Number(b?.blended_score || 0) - Number(a?.blended_score || 0)
        );
    }
  }, [trustedResults, sortBy]);

  const bestRecommendation = trustedResults.length > 0 ? trustedResults[0] : null;

  return (
    <div className="w-full max-w-5xl mx-auto px-4 py-8">
      {/* Search Meta Strip */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-5 mb-6 border-b border-slate-800 gap-3">
        <div>
          <h2 className="text-xl md:text-2xl font-bold text-slate-100 flex items-center space-x-2">
            <span>Results for</span>
            <span className="text-emerald-400">"{query || 'Product'}"</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Listings found from public search results. Check the retailer page before buying.
          </p>
        </div>

        {/* Total found & Processing time badge */}
        <div className="flex items-center space-x-3 text-xs">
          <span className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-300 font-mono">
            <strong>{totalFound}</strong> listings found
          </span>
          <span className="px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 font-mono flex items-center space-x-1.5">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span>{(processingTimeMs / 1000).toFixed(2)}s</span>
          </span>
        </div>
      </div>

      {data?.metadata?.notice && (
        <div className="mb-5 rounded-xl border border-amber-500/30 bg-amber-950/25 px-4 py-3 text-sm text-amber-100">
          {data.metadata.notice}
        </div>
      )}

      {results.length === 0 && (
        <div className="mb-5 rounded-xl border border-slate-700 bg-slate-900/60 px-5 py-6">
          <h3 className="font-semibold text-slate-100">No comparable live listings were available</h3>
          <p className="mt-1 text-sm text-slate-400">
            {data?.metadata?.search_status === 'provider_error'
              ? `The search provider could not be reached. ${data?.metadata?.search_errors?.[0] || 'Check backend internet access and retry.'}`
              : data?.metadata?.candidate_urls > 0
                ? `${data.metadata.candidate_urls} candidate pages were found; ${data.metadata.price_unavailable || 0} did not expose a usable product price and ${data.metadata.scrape_failures || 0} could not be fetched. Try again or check the retailer directly.`
                : 'The search provider returned no candidate product links. Try a more specific product name or retry when the search service is available.'}
          </p>
        </div>
      )}

      {/* Tabs & Sorting Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        {/* Two Tabs: Trusted vs Discarded */}
        <div className="flex items-center p-1 rounded-xl bg-slate-900/90 border border-slate-800 self-start sm:self-auto">
          {/* Trusted Tab */}
          <button
            type="button"
            onClick={() => setActiveTab('trusted')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-semibold text-xs md:text-sm transition-all duration-200 ${
              activeTab === 'trusted'
                ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>✅ Meets {Math.round(minimumTrust * 100)}% Threshold</span>
            <span
              className={`px-1.5 py-0.5 rounded-full text-xs font-mono font-bold ${
                activeTab === 'trusted'
                  ? 'bg-emerald-500 text-slate-950'
                  : 'bg-slate-800 text-slate-400'
              }`}
            >
              {trustedResults.length}
            </span>
          </button>

          {/* Discarded Tab */}
          <button
            type="button"
            onClick={() => setActiveTab('discarded')}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-semibold text-xs md:text-sm transition-all duration-200 ${
              activeTab === 'discarded'
                ? 'bg-red-500/20 text-red-400 border border-red-500/40 shadow-sm'
                : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            <Ban className="w-4 h-4 text-red-400" />
            <span>❌ Discarded Results</span>
            <span
              className={`px-1.5 py-0.5 rounded-full text-xs font-mono font-bold ${
                activeTab === 'discarded'
                  ? 'bg-red-500 text-white'
                  : 'bg-slate-800 text-slate-400'
              }`}
            >
              {discardedResults.length}
            </span>
          </button>
        </div>

        {/* Sort Selector (for Trusted tab) */}
        {activeTab === 'trusted' && trustedResults.length > 1 && (
          <div className="flex items-center space-x-2 text-xs">
            <span className="text-slate-400 flex items-center space-x-1">
              <ArrowUpDown className="w-3.5 h-3.5" />
              <span>Sort:</span>
            </span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded-lg px-2.5 py-1.5 text-slate-200 text-xs focus:outline-none focus:border-emerald-500"
            >
              <option value="trust">Highest Trust Score</option>
              <option value="blended">Blended Relevance + Trust</option>
              <option value="price_asc">Price: Low to High</option>
              <option value="price_desc">Price: High to Low</option>
            </select>
          </div>
        )}
      </div>

      {/* Tab 1: Trusted Results */}
      {activeTab === 'trusted' && (
        <div className="space-y-4">
          {sortedTrusted.length > 0 ? (
            sortedTrusted.map((item, idx) => (
              <ProductCard key={item.product?.id || idx} item={item} />
            ))
          ) : (
            <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800">
              <AlertCircle className="w-10 h-10 text-amber-400 mx-auto mb-3" />
              <h3 className="text-base font-bold text-slate-200 mb-1">
                No Trusted Results Found
              </h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                No listings are available in this tab. If the live result count is zero, the search did not discover any product pages.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Tab 2: Discarded Results */}
      {activeTab === 'discarded' && (
        <div className="space-y-4">
          {discardedResults.length > 0 ? (
            discardedResults.map((item, idx) => (
              <DiscardedCard key={item.product?.id || idx} item={item} />
            ))
          ) : (
            <div className="p-12 text-center rounded-2xl bg-slate-900/40 border border-slate-800">
              <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto mb-3" />
              <h3 className="text-base font-bold text-slate-200 mb-1">
                Zero Discarded Listings
              </h3>
              <p className="text-xs text-slate-400 max-w-md mx-auto">
                No listings were flagged in this tab. This does not certify that any product or store is safe.
              </p>
            </div>
          )}
        </div>
      )}

      {/* Summary Section at the Bottom */}
      <Summary
        trustedResults={trustedResults}
        discardedResults={discardedResults}
        processingTimeMs={processingTimeMs}
        bestRecommendation={bestRecommendation}
      />
    </div>
  );
}
