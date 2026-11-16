import React, { useState, useEffect } from 'react';
import { ShieldCheck, ShieldAlert, Lock, Globe, MessageSquare, Sparkles } from 'lucide-react';

const STEPS = [
  { icon: Globe, text: 'Querying e-commerce platforms & product listings...' },
  { icon: Lock, text: 'Inspecting SSL certificates, TLS versions, & domain WHOIS...' },
  { icon: MessageSquare, text: 'Analyzing Reddit threads, buyer discussions & sentiment...' },
  { icon: ShieldCheck, text: 'Verifying seller credentials & calculating anomaly scores...' },
  { icon: Sparkles, text: 'Synthesizing evidence trails & ranking verified products...' },
];

/**
 * High-tech Loading Spinner with spinning shield and rotating verification steps
 */
export default function LoadingSpinner() {
  const [stepIndex, setStepIndex] = useState(0);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    // Rotate through status messages every 2.4s
    const stepInterval = setInterval(() => {
      setStepIndex((prev) => (prev + 1) % STEPS.length);
    }, 2400);

    // Track elapsed seconds
    const timerInterval = setInterval(() => {
      setElapsed((prev) => prev + 1);
    }, 1000);

    return () => {
      clearInterval(stepInterval);
      clearInterval(timerInterval);
    };
  }, []);

  const CurrentStep = STEPS[stepIndex];
  const StepIcon = CurrentStep.icon;

  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      {/* Outer Glow & Spinning Shield */}
      <div className="relative flex items-center justify-center mb-8">
        {/* Pulsing ring */}
        <div className="absolute w-28 h-28 rounded-full bg-emerald-500/10 border border-emerald-500/20 animate-ping" />
        
        {/* Rotating dash ring */}
        <div className="w-24 h-24 rounded-full border-2 border-dashed border-emerald-500/40 animate-spin-slow flex items-center justify-center" />

        {/* Inner shield icon */}
        <div className="absolute flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-tr from-emerald-950 to-slate-900 border border-emerald-500/50 shadow-xl shadow-emerald-500/20">
          <ShieldCheck className="w-9 h-9 text-emerald-400 animate-pulse" />
        </div>
      </div>

      {/* Title */}
      <h3 className="text-lg md:text-xl font-bold text-slate-100 tracking-tight mb-2">
        Verifying Product Authenticity & Trust
      </h3>

      {/* Rotating Step Box */}
      <div className="flex items-center space-x-2.5 px-4 py-2 rounded-full bg-slate-900/90 border border-slate-800 text-xs md:text-sm text-slate-300 shadow-md">
        <StepIcon className="w-4 h-4 text-emerald-400 animate-bounce" />
        <span className="transition-all duration-300 font-medium">{CurrentStep.text}</span>
      </div>

      {/* Pulsing Dots & Timer */}
      <div className="mt-5 flex items-center space-x-2 text-xs text-slate-500 font-mono">
        <div className="flex space-x-1">
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-bounce" style={{ animationDelay: '0ms' }} />
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-bounce" style={{ animationDelay: '150ms' }} />
          <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
        <span>Elapsed: {elapsed}s</span>
      </div>
    </div>
  );
}
