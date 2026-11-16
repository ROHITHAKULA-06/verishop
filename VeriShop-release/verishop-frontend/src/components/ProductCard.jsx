import React, { useState } from 'react';
import {
  ExternalLink,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Award,
  Sparkles,
  ShoppingBag,
} from 'lucide-react';
import TrustGauge from './TrustGauge.jsx';
import TrustBreakdown from './TrustBreakdown.jsx';

/**
 * Format currency into INR style (e.g., ₹1,29,999)
 */
function formatPrice(price, currency = 'INR') {
  if (price === undefined || price === null || isNaN(Number(price))) {
    return 'Price unavailable';
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
 * Extract clean domain name from URL or string
 */
function cleanDomain(sourceName = '', url = '') {
  if (sourceName && !sourceName.startsWith('http')) {
    return sourceName.replace(/^www\./i, '');
  }
  try {
    const parsed = new URL(url.startsWith('http') ? url : `https://${url}`);
    return parsed.hostname.replace(/^www\./i, '');
  } catch {
    return sourceName || 'Direct Store';
  }
}

/**
 * ProductCard component for Trusted & Caution products
 *
 * @param {Object} props
 * @param {Object} props.item - RankedProduct object
 */
export default function ProductCard({ item }) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [imgError, setImgError] = useState(false);

  const product = item?.product || {};
  const trustScore = item?.trust_score || {};
  const source = product.source || {};
  const pricing = product.pricing || {};
  const images = Array.isArray(product.images) ? product.images : [];
  const primaryImg = images.find((img) => img.is_primary) || images[0];

  const domain = cleanDomain(source.source_name, source.source_url);
  const targetUrl = source.source_url || '#';

  const verdict = (trustScore.verdict || 'TRUSTED').toUpperCase();
  const overallScore = Number(trustScore.overall_score || 0);

  // Verdict Badge Styling
  const verdictConfig = {
    TRUSTED: {
      label: 'TRUSTED',
      badgeClass: 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30',
      icon: <ShieldCheck className="w-3.5 h-3.5" />,
    },
    CAUTION: {
      label: 'CAUTION',
      badgeClass: 'bg-amber-500/15 text-amber-400 border-amber-500/30',
      icon: <AlertTriangle className="w-3.5 h-3.5" />,
    },
    UNTRUSTED: {
      label: 'UNTRUSTED',
      badgeClass: 'bg-red-500/15 text-red-400 border-red-500/30',
      icon: <ShieldAlert className="w-3.5 h-3.5" />,
    },
  }[verdict] || {
    label: verdict,
    badgeClass: 'bg-slate-700/40 text-slate-300 border-slate-600',
    icon: <ShieldCheck className="w-3.5 h-3.5" />,
  };

  const relevancePct = Math.round((Number(item.relevance_score) || 0) * 100);
  const blendedPct = Math.round((Number(item.blended_score) || 0) * 100);

  // Favicon URL with fallback
  const faviconUrl = domain ? `https://www.google.com/s2/favicons?domain=${domain}&sz=64` : null;

  return (
    <div className="group rounded-xl bg-slate-900/90 border border-slate-800 hover:border-slate-700/80 shadow-lg shadow-black/40 transition-all duration-300 overflow-hidden">
      {/* Top Card Body */}
      <div className="p-5 md:p-6 flex flex-col md:flex-row gap-5 items-start">
        {/* Product Image Thumbnail */}
        <div className="relative w-full md:w-36 h-36 flex-shrink-0 rounded-lg overflow-hidden bg-slate-950 border border-slate-800 flex items-center justify-center group-hover:border-slate-700 transition-colors">
          {primaryImg?.url && !imgError ? (
            <img
              src={primaryImg.url}
              alt={product.title || 'Product'}
              onError={() => setImgError(true)}
              className="w-full h-full object-cover object-center group-hover:scale-105 transition-transform duration-300"
              loading="lazy"
            />
          ) : (
            <div className="flex flex-col items-center justify-center text-slate-600 p-3 text-center">
              <ShoppingBag className="w-8 h-8 mb-1 text-slate-500" />
              <span className="text-[10px] text-slate-500">Image Preview</span>
            </div>
          )}

          {/* Rank Badge */}
          {item.rank ? (
            <div className="absolute top-2 left-2 px-2 py-0.5 rounded bg-black/80 backdrop-blur-md border border-slate-700 text-[11px] font-mono font-bold text-slate-200">
              #{item.rank}
            </div>
          ) : null}
        </div>

        {/* Product Details & Title */}
        <div className="flex-1 min-w-0 flex flex-col justify-between">
          <div>
            {/* Domain & Source row */}
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <div className="inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-slate-800/80 border border-slate-700/80 text-xs text-slate-300">
                {faviconUrl && (
                  <img
                    src={faviconUrl}
                    alt=""
                    className="w-3.5 h-3.5 rounded-sm object-contain"
                    onError={(e) => { e.target.style.display = 'none'; }}
                  />
                )}
                <span className="font-medium tracking-wide">{domain}</span>
              </div>

              {/* Verdict Badge */}
              <div
                className={`inline-flex items-center space-x-1 px-2.5 py-1 rounded-md text-xs font-semibold tracking-wider border ${verdictConfig.badgeClass}`}
              >
                {verdictConfig.icon}
                <span>{verdictConfig.label}</span>
              </div>

              {product.seller_name && (
                <div className="inline-flex items-center text-xs text-slate-400 truncate max-w-xs">
                  <Award className="w-3 h-3 mr-1 text-slate-500" />
                  <span className="truncate">{product.seller_name}</span>
                </div>
              )}
            </div>

            {/* Product Title (clickable link) */}
            <h3 className="text-base md:text-lg font-bold text-slate-100 hover:text-emerald-400 transition-colors leading-snug line-clamp-2 mb-2">
              <a
                href={targetUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1.5 group/link"
              >
                <span>{product.title || 'Untitled Product'}</span>
                <ExternalLink className="w-4 h-4 opacity-50 group-hover/link:opacity-100 transition-opacity flex-shrink-0" />
              </a>
            </h3>

            {/* Description snippet */}
            {product.description && (
              <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed mb-3">
                {product.description}
              </p>
            )}
          </div>

          {/* Price & Score Tags Footer */}
          <div className="flex flex-wrap items-baseline justify-between gap-3 pt-2 border-t border-slate-800/60">
            {/* Price section */}
            <div className="flex items-baseline space-x-2">
              <span className="text-xl md:text-2xl font-black font-mono text-emerald-400">
                {Number(pricing.price) > 0
                  ? formatPrice(pricing.price, pricing.currency)
                  : 'Price unavailable'}
              </span>
              {pricing.original_price && pricing.original_price > pricing.price && (
                <span className="text-xs font-mono text-slate-500 line-through">
                  {formatPrice(pricing.original_price, pricing.currency)}
                </span>
              )}
              {pricing.discount_pct && (
                <span className="text-[11px] font-semibold text-emerald-500 bg-emerald-500/10 px-1.5 py-0.5 rounded">
                  {Math.round(pricing.discount_pct)}% off
                </span>
              )}
            </div>

            {/* Relevance & Blended Scores */}
            <div className="flex items-center space-x-2 text-xs">
              <span
                className="px-2 py-1 rounded bg-slate-800/90 text-slate-300 font-mono border border-slate-700/80"
                title="Semantic Relevance to your search query"
              >
                Relevance: <strong className="text-white">{relevancePct}%</strong>
              </span>
              <span
                className="px-2 py-1 rounded bg-blue-950/40 text-blue-300 font-mono border border-blue-500/30 flex items-center space-x-1"
                title="Blended Rank combining Relevance and Trust"
              >
                <Sparkles className="w-3 h-3 text-blue-400" />
                <span>Blended: <strong>{blendedPct}%</strong></span>
              </span>
            </div>
          </div>
        </div>

        {/* Circular Trust Score Gauge */}
        <div className="w-full md:w-auto flex md:flex-col items-center justify-between md:justify-center p-3 md:p-4 rounded-xl bg-slate-950/60 border border-slate-800/80 flex-shrink-0 self-stretch md:self-auto gap-2">
          <div className="flex flex-col items-start md:items-center">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 mb-1">
              Trust Score
            </span>
            <span className="text-[10px] text-slate-500 hidden md:block">
              Multi-factor AI
            </span>
          </div>
          <TrustGauge score={overallScore} size="md" showLabel={false} />
          <a
            href={targetUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="md:hidden inline-flex items-center space-x-1 text-xs text-emerald-400 font-medium hover:underline"
          >
            <span>Visit Store</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>

      {/* Expandable Toggle Button */}
      <div className="px-5 py-2.5 bg-slate-950/40 border-t border-slate-800/60 flex items-center justify-between text-xs text-slate-400">
        <button
          type="button"
          onClick={() => setIsExpanded(!isExpanded)}
          className="inline-flex items-center space-x-1.5 font-medium text-slate-300 hover:text-emerald-400 transition-colors focus:outline-none"
        >
          <span>{isExpanded ? 'Hide Trust Breakdown' : 'View Trust Breakdown & Evidence'}</span>
          {isExpanded ? (
            <ChevronUp className="w-4 h-4 text-emerald-400" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>

        <a
          href={targetUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="hidden md:inline-flex items-center space-x-1 text-slate-400 hover:text-white transition-colors"
        >
          <span>Open on {domain}</span>
          <ExternalLink className="w-3.5 h-3.5" />
        </a>
      </div>

      {/* Expanded Trust Breakdown Details */}
      {isExpanded && (
        <div className="px-5 pb-5 pt-1 bg-slate-950/70 border-t border-slate-800/60 animate-fadeIn">
          <TrustBreakdown trustScore={trustScore} />
        </div>
      )}
    </div>
  );
}
