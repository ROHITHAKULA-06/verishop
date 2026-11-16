/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: {
          DEFAULT: '#0B0F19',
          surface: '#111827',
          card: '#161F30',
          subtle: '#1E293B',
          border: '#2A364F',
        },
        trust: {
          trusted: '#10B981',      // Emerald 500
          trustedBg: 'rgba(16, 185, 129, 0.1)',
          trustedBorder: 'rgba(16, 185, 129, 0.3)',
          caution: '#F59E0B',      // Amber 500
          cautionBg: 'rgba(245, 158, 11, 0.1)',
          cautionBorder: 'rgba(245, 158, 11, 0.3)',
          untrusted: '#EF4444',    // Red 500
          untrustedBg: 'rgba(239, 68, 68, 0.1)',
          untrustedBorder: 'rgba(239, 68, 68, 0.3)',
        },
      },
      animation: {
        'pulse-subtle': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'spin-slow': 'spin 8s linear infinite',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
    },
  },
  plugins: [],
};
