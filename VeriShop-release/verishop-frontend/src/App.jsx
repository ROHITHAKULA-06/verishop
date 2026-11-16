import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Shield,
  Activity,
  AlertCircle,
  Sparkles,
  Lock,
  Globe,
  MessageSquare,
  RefreshCw,
  Cpu,
  Layers,
  CheckCircle2,
} from 'lucide-react';
import SearchBar from './components/SearchBar.jsx';
import LoadingSpinner from './components/LoadingSpinner.jsx';
import ResultsDisplay from './components/ResultsDisplay.jsx';
import { searchProducts, checkBackendHealth, getMockSearchResults } from './utils/api.js';

export default function App() {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [backendStatus, setBackendStatus] = useState('checking'); // 'online' | 'offline' | 'checking'
  const [isDemoMode, setIsDemoMode] = useState(false);

  // Check backend health on initial load
  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    setBackendStatus('checking');
    try {
      await checkBackendHealth();
      setBackendStatus('online');
    } catch {
      setBackendStatus('offline');
    }
  };

  const handleSearch = async (params) => {
    const searchQuery = params.query || query;
    setQuery(searchQuery);
    setIsLoading(true);
    setError(null);

    // If already in demo mode or user clicked demo, load mock
    if (isDemoMode) {
      setTimeout(() => {
        const mockData = getMockSearchResults(searchQuery);
        setSearchResults(mockData);
        setIsLoading(false);
      }, 900);
      return;
    }

    try {
      const data = await searchProducts(params);
      setSearchResults({
        ...data,
        metadata: {
          ...(data.metadata || {}),
          min_trust_score: Number(params.min_trust_score ?? 0.5),
        },
      });
      setBackendStatus('online');
    } catch (err) {
      console.error('Search error:', err);
      setError({
        message: err.message || 'An error occurred during verification.',
        isNetwork: err.isNetworkError || err.message.includes('Unable to connect') || err.message.includes('fetch'),
      });
      // Update health status if network error
      if (err.isNetworkError || err.message.includes('Unable to connect')) {
        setBackendStatus('offline');
      }
    } finally {
      setIsLoading(false);
    }
  };

  const loadDemoData = (targetQuery = 'iPhone 15 Pro') => {
    setIsDemoMode(true);
    setError(null);
    setIsLoading(true);
    setQuery(targetQuery);
    setTimeout(() => {
      setSearchResults(getMockSearchResults(targetQuery));
      setIsLoading(false);
    }, 600);
  };

  return (
    <div className="min-h-screen bg-[#0B0F19] text-slate-100 flex flex-col selection:bg-emerald-500 selection:text-white">
      {/* Top Navbar */}
      <header className="sticky top-0 z-40 bg-[#0B0F19]/90 backdrop-blur-md border-b border-slate-800/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          {/* Logo & Brand */}
          <div
            onClick={() => {
              setSearchResults(null);
              setError(null);
            }}
            className="flex items-center space-x-3 cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-600 to-teal-400 p-0.5 shadow-lg shadow-emerald-500/20 group-hover:shadow-emerald-500/40 transition-shadow">
              <div className="w-full h-full bg-slate-950 rounded-[10px] flex items-center justify-center">
                <ShieldCheck className="w-5 h-5 text-emerald-400" />
              </div>
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="text-lg font-black tracking-tight text-white">
                  Veri<span className="text-emerald-400">Shop</span>
                </span>
                <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  v1.0
                </span>
              </div>
              <p className="text-[10px] text-slate-400 tracking-wider uppercase font-semibold hidden sm:block">
                Trust-Aware Product Verification
              </p>
            </div>
          </div>

          {/* Right Header Badges */}
          <div className="flex items-center space-x-3 text-xs">
            {/* Backend Health Indicator */}
            <div
              className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full border text-xs font-mono transition-colors ${
                backendStatus === 'online'
                  ? 'bg-emerald-950/40 border-emerald-500/30 text-emerald-400'
                  : backendStatus === 'checking'
                  ? 'bg-amber-950/40 border-amber-500/30 text-amber-400'
                  : 'bg-red-950/40 border-red-500/30 text-red-400'
              }`}
              title="API Backend Status (http://localhost:8000)"
            >
              <div
                className={`w-2 h-2 rounded-full ${
                  backendStatus === 'online'
                    ? 'bg-emerald-400 animate-pulse'
                    : backendStatus === 'checking'
                    ? 'bg-amber-400 animate-ping'
                    : 'bg-red-400'
                }`}
              />
              <span className="hidden sm:inline">
                {backendStatus === 'online'
                  ? 'Backend Connected'
                  : backendStatus === 'checking'
                  ? 'Checking API...'
                  : 'Backend Offline'}
              </span>
              <button
                type="button"
                onClick={checkHealth}
                className="hover:rotate-180 transition-transform duration-300 ml-0.5"
                title="Refresh API Health"
              >
                <RefreshCw className="w-3 h-3 text-slate-400 hover:text-white" />
              </button>
            </div>

            {/* Demo Mode Toggle Button */}
            <button
              type="button"
              onClick={() => {
                if (isDemoMode) {
                  setIsDemoMode(false);
                  setSearchResults(null);
                } else {
                  loadDemoData();
                }
              }}
              className={`px-3 py-1 rounded-full text-xs font-semibold border transition-all ${
                isDemoMode
                  ? 'bg-blue-600/30 border-blue-500 text-blue-300 shadow-md shadow-blue-500/20'
                  : 'bg-slate-800 hover:bg-slate-700 border-slate-700 text-slate-300'
              }`}
            >
              {isDemoMode ? '✨ Demo Mode Active' : 'Load Demo Data'}
            </button>
          </div>
        </div>
      </header>

      {/* Hero / Header Section */}
      <main className="flex-1 flex flex-col">
        <section className="pt-10 pb-6 text-center relative overflow-hidden">
          {/* Subtle Background Glow Elements */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[550px] h-[250px] bg-gradient-to-r from-emerald-500/10 via-teal-500/10 to-blue-500/10 rounded-full blur-3xl pointer-events-none" />

          <div className="max-w-4xl mx-auto px-4 relative z-10">
            <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-semibold uppercase tracking-wider mb-4">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Multi-Source Trust Intelligence</span>
            </div>

            <h1 className="text-3xl sm:text-4xl md:text-5xl font-black text-white tracking-tight leading-tight mb-3">
              Shop with verified <span className="bg-gradient-to-r from-emerald-400 to-teal-300 bg-clip-text text-transparent">confidence</span>.
            </h1>

            <p className="text-sm md:text-base text-slate-400 max-w-2xl mx-auto mb-8 leading-relaxed">
              Compare live public listings and inspect the signals behind each score. Retailer pages
              vary by region and access policy, so every extracted price should be checked at the store.
            </p>

            {/* Main Search Component */}
            <SearchBar
              onSearch={handleSearch}
              isLoading={isLoading}
              initialQuery={query}
            />
          </div>
        </section>

        {/* Dynamic States: Loading, Error, Results, or Empty Hero */}
        <section className="flex-1">
          {/* Loading Animation */}
          {isLoading && <LoadingSpinner />}

          {/* Error Banner */}
          {error && !isLoading && (
            <div className="w-full max-w-3xl mx-auto px-4 my-6">
              <div className="p-5 rounded-2xl bg-red-950/40 border border-red-500/40 shadow-xl text-red-200">
                <div className="flex items-start space-x-3">
                  <AlertCircle className="w-6 h-6 text-red-400 mt-0.5 flex-shrink-0" />
                  <div className="flex-1">
                    <h3 className="text-sm font-bold text-red-300 mb-1">
                      {error.isNetwork ? 'Backend Connection Error' : 'Search Request Failed'}
                    </h3>
                    <p className="text-xs text-red-200/90 leading-relaxed mb-3">
                      {error.message}
                    </p>

                    {error.isNetwork && (
                      <div className="p-3 rounded-lg bg-black/40 border border-red-900/50 text-[11px] font-mono text-slate-300 space-y-1 mb-4">
                        <p className="text-slate-400">To start the backend server, execute:</p>
                        <p className="text-emerald-400 font-bold">Start the API from the project’s verishop-backend folder (see README).</p>
                      </div>
                    )}

                    <div className="flex flex-wrap items-center gap-3">
                      <button
                        type="button"
                        onClick={() => loadDemoData(query || 'iPhone 15 Pro')}
                        className="px-4 py-2 rounded-xl bg-red-500 hover:bg-red-400 text-slate-950 font-bold text-xs shadow-md transition-colors flex items-center space-x-1.5"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>Explore with Demo Data Instead</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => handleSearch({ query })}
                        className="px-3 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 font-medium text-xs transition-colors"
                      >
                        Retry Search
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Results Display */}
          {searchResults && !isLoading && !error && (
            <ResultsDisplay data={searchResults} query={query} />
          )}

          {/* Default Empty State: Explaining VeriShop's 4 Pillars */}
          {!searchResults && !isLoading && !error && (
            <div className="w-full max-w-5xl mx-auto px-4 py-12">
              <div className="text-center mb-8">
                <h3 className="text-xs uppercase font-bold tracking-widest text-emerald-400 mb-1">
                  How VeriShop Protects You
                </h3>
                <h2 className="text-xl md:text-2xl font-bold text-slate-200">
                  Four Layers of Automated Due Diligence
                </h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {/* Pillar 1 */}
                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all duration-300 group">
                  <div className="w-10 h-10 rounded-xl bg-sky-500/10 border border-sky-500/20 text-sky-400 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                    <Lock className="w-5 h-5" />
                  </div>
                  <h4 className="text-sm font-bold text-slate-100 mb-1.5">
                    SSL & Network Security
                  </h4>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Checks the available transport and domain signals. A valid HTTPS connection alone does not prove a store or listing is legitimate.
                  </p>
                </div>

                {/* Pillar 2 */}
                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all duration-300 group">
                  <div className="w-10 h-10 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                    <Globe className="w-5 h-5" />
                  </div>
                  <h4 className="text-sm font-bold text-slate-100 mb-1.5">
                    Domain Age & WHOIS
                  </h4>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Uses domain registration data when available; privacy protection and registry limits can make these signals incomplete.
                  </p>
                </div>

                {/* Pillar 3 */}
                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all duration-300 group">
                  <div className="w-10 h-10 rounded-xl bg-orange-500/10 border border-orange-500/20 text-orange-400 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                    <MessageSquare className="w-5 h-5" />
                  </div>
                  <h4 className="text-sm font-bold text-slate-100 mb-1.5">
                    Reddit Sentiment Mining
                  </h4>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Combines available seller and review signals. Community sentiment is not a guarantee of product authenticity or delivery.
                  </p>
                </div>

                {/* Pillar 4 */}
                <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 hover:border-slate-700 transition-all duration-300 group">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center justify-center mb-3 group-hover:scale-110 transition-transform">
                    <Cpu className="w-5 h-5" />
                  </div>
                  <h4 className="text-sm font-bold text-slate-100 mb-1.5">
                    Multimodal Deep Learning
                  </h4>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Matching and scoring help organize listings. Scores are estimates and should be reviewed alongside the evidence shown.
                  </p>
                </div>
              </div>

              {/* Demo Action Banner */}
              <div className="mt-8 text-center">
                <button
                  type="button"
                  onClick={() => loadDemoData('iPhone 15 Pro')}
                  className="inline-flex items-center space-x-2 px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-semibold text-slate-200 transition-all shadow-md"
                >
                  <Sparkles className="w-4 h-4 text-emerald-400" />
                  <span>Explore Sample Verification Dashboard</span>
                </button>
              </div>
            </div>
          )}
        </section>
      </main>

      {/* Footer */}
      <footer className="mt-auto border-t border-slate-900 bg-slate-950/70 py-6 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            <span className="font-semibold text-slate-400">VeriShop</span>
            <span>— Trust-Aware Online Shopping and Product Verification</span>
          </div>

          <div className="flex items-center space-x-4 text-slate-400">
            <span>FastAPI Backend: <code className="text-slate-300 font-mono">http://localhost:8000</code></span>
            <span>•</span>
            <span>React + Vite + Tailwind</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
