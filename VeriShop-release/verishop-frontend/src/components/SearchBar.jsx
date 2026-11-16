import React, { useState, useRef } from 'react';
import {
  Search,
  Image as ImageIcon,
  SlidersHorizontal,
  X,
  Sparkles,
  ShieldCheck,
  Upload,
} from 'lucide-react';

const SUGGESTED_QUERIES = [
  'iPhone 15 Pro',
  'Sony WH-1000XM5',
  'Nike Air Max Sneakers',
  'MacBook Air M2',
  'Rolex Submariner Watch',
];

/**
 * SearchBar Component
 *
 * @param {Object} props
 * @param {Function} props.onSearch - Callback when search is submitted ({ query, min_trust_score, max_results, image_base64 })
 * @param {boolean} props.isLoading - Whether a search is currently in progress
 * @param {string} [props.initialQuery='']
 */
export default function SearchBar({ onSearch, isLoading, initialQuery = '' }) {
  const [query, setQuery] = useState(initialQuery);
  const [minTrustScore, setMinTrustScore] = useState(0.0);
  const [maxResults, setMaxResults] = useState(50);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedImage, setSelectedImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);

  const fileInputRef = useRef(null);

  const handleSubmit = (e) => {
    e?.preventDefault();
    if ((!query || !query.trim()) && !selectedImage) {
      return;
    }
    onSearch({
      query: query.trim(),
      min_trust_score: Number(minTrustScore),
      max_results: Number(maxResults),
      image_base64: selectedImage,
    });
  };

  const handleChipClick = (suggestion) => {
    setQuery(suggestion);
    onSearch({
      query: suggestion,
      min_trust_score: Number(minTrustScore),
      max_results: Number(maxResults),
      image_base64: selectedImage,
    });
  };

  const handleImageChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64String = reader.result;
        setSelectedImage(base64String);
        setImagePreview(base64String);
      };
      reader.readAsDataURL(file);
    }
  };

  const removeImage = () => {
    setSelectedImage(null);
    setImagePreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4">
      {/* Search Input Container */}
      <form onSubmit={handleSubmit} className="relative">
        <div className="relative flex items-center rounded-2xl bg-slate-900/90 border border-slate-700/80 shadow-2xl shadow-blue-950/20 focus-within:border-emerald-500 focus-within:ring-2 focus-within:ring-emerald-500/20 transition-all duration-300">
          {/* Left Search Icon */}
          <div className="pl-4 md:pl-5 text-slate-400 flex items-center pointer-events-none">
            <Search className="w-5 h-5 md:w-6 md:h-6 text-slate-400 group-focus-within:text-emerald-400" />
          </div>

          {/* Text Input */}
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={isLoading}
            placeholder="Search for any product (e.g. iPhone 15 Pro, Sony Headphones)..."
            className="w-full py-4 px-3 md:px-4 bg-transparent text-slate-100 placeholder-slate-500 text-sm md:text-base focus:outline-none disabled:opacity-50"
          />

          {/* Clear text button */}
          {query && !isLoading && (
            <button
              type="button"
              onClick={() => setQuery('')}
              className="p-1 text-slate-400 hover:text-slate-200 transition-colors mr-1"
              title="Clear search text"
            >
              <X className="w-4 h-4" />
            </button>
          )}

          {/* Right Action Buttons */}
          <div className="flex items-center space-x-1.5 pr-2 md:pr-3">
            {/* Image upload button */}
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleImageChange}
              accept="image/*"
              className="hidden"
            />
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className={`p-2.5 rounded-xl transition-all duration-200 ${
                imagePreview
                  ? 'bg-blue-600/30 text-blue-400 border border-blue-500/40'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
              title={imagePreview ? 'Change uploaded image' : 'Upload product image (Visual verification)'}
            >
              <ImageIcon className="w-5 h-5" />
            </button>

            {/* Filter Toggle */}
            <button
              type="button"
              onClick={() => setShowFilters(!showFilters)}
              className={`p-2.5 rounded-xl transition-all duration-200 ${
                showFilters || minTrustScore > 0
                  ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800'
              }`}
              title="Toggle search filters"
            >
              <SlidersHorizontal className="w-5 h-5" />
            </button>

            {/* Primary Search Button */}
            <button
              type="submit"
              disabled={isLoading || ((!query || !query.trim()) && !selectedImage)}
              className="px-4 md:px-6 py-2.5 md:py-3 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-slate-950 font-bold text-sm md:text-base flex items-center space-x-2 shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/40 transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:shadow-none"
            >
              {isLoading ? (
                <>
                  <div className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                  <span className="hidden md:inline">Verifying...</span>
                </>
              ) : (
                <>
                  <span>Verify</span>
                  <ShieldCheck className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>

        {/* Selected Image Preview Pill */}
        {imagePreview && (
          <div className="mt-2.5 inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-900 border border-slate-700 text-xs text-slate-300">
            <img
              src={imagePreview}
              alt="Uploaded visual query"
              className="w-6 h-6 rounded object-cover border border-slate-600"
            />
            <span className="truncate max-w-xs">Visual Query Active</span>
            <button
              type="button"
              onClick={removeImage}
              className="text-slate-400 hover:text-red-400 transition-colors ml-1"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        )}

        {/* Expandable Advanced Filters Drawer */}
        {showFilters && (
          <div className="mt-3 p-4 rounded-xl bg-slate-900/95 border border-slate-800 backdrop-blur-md shadow-xl text-xs space-y-4 animate-fadeIn">
            <div className="flex items-center justify-between pb-2 border-b border-slate-800">
              <span className="font-semibold text-slate-200 uppercase tracking-wider text-[11px]">
                Search & Trust Parameters
              </span>
              <button
                type="button"
                onClick={() => {
                  setMinTrustScore(0.0);
                  setMaxResults(10);
                }}
                className="text-slate-400 hover:text-emerald-400 transition-colors"
              >
                Reset to default
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Min Trust Score Slider */}
              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="text-slate-300 font-medium">
                    Minimum Trust Score Filter:
                  </label>
                  <span className="font-mono font-bold text-emerald-400">
                    {Math.round(minTrustScore * 100)}%
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="0.9"
                  step="0.05"
                  value={minTrustScore}
                  onChange={(e) => setMinTrustScore(parseFloat(e.target.value))}
                  className="w-full accent-emerald-500 bg-slate-800 h-1.5 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-[10px] text-slate-500 mt-1">
                  <span>0% (Show All)</span>
                  <span>50% (Caution+)</span>
                  <span>80% (Strict)</span>
                </div>
              </div>

              {/* Max Results */}
              <div>
                <label className="text-slate-300 font-medium block mb-1">
                  Max Listings Analyzed:
                </label>
                <div className="flex space-x-2">
                  {[20, 50, 100].map((count) => (
                    <button
                      key={count}
                      type="button"
                      onClick={() => setMaxResults(count)}
                      className={`flex-1 py-1.5 rounded-lg border font-mono font-medium transition-all ${
                        maxResults === count
                          ? 'bg-emerald-500/20 border-emerald-500/60 text-emerald-400'
                          : 'bg-slate-800/60 border-slate-700 text-slate-400 hover:text-slate-200'
                      }`}
                    >
                      {count} items
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}
      </form>

      {/* Suggested Search Chips */}
      <div className="mt-3 flex flex-wrap items-center gap-2 justify-center">
        <span className="text-xs text-slate-400 flex items-center mr-1">
          <Sparkles className="w-3 h-3 text-amber-400 mr-1" />
          Try:
        </span>
        {SUGGESTED_QUERIES.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            onClick={() => handleChipClick(suggestion)}
            disabled={isLoading}
            className="px-2.5 py-1 rounded-full bg-slate-900/80 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-xs text-slate-400 hover:text-emerald-300 transition-all duration-200 disabled:opacity-50"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}
