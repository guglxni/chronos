/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // PlayStation-inspired palette — our dark backgrounds stay the same,
        // the accent moves from sky-* to ps-* so primary actions match the
        // brand anchor (#0070cc) and hover states pulse cyan (#1eaedb).
        ps: {
          blue: '#0070cc',       // brand anchor
          cyan: '#1eaedb',       // hover / focus only
          link: '#1883fd',       // link hover on light
          dark: '#0068bd',       // link at rest on light
          darklink: '#53b1ff',   // link at rest on dark (our default)
          orange: '#d53b00',     // commerce / destructive emphasis
          charcoal: '#1f1f1f',   // body headline ink
        },
        // Retained for drop-in compatibility with existing sky-* classes.
        chronos: {
          50:  '#f0f9ff',
          100: '#e0f2fe',
          200: '#bae6fd',
          300: '#7dd3fc',
          400: '#38bdf8',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
          800: '#075985',
          900: '#0c4a6e',
        },
      },
      fontFamily: {
        display: ['"Inter"', 'system-ui', '-apple-system', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.3s ease-out forwards',
        'shimmer': 'shimmer 1.5s linear infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
      },
      boxShadow: {
        // PlayStation "power-on ring" signature hover
        'ps-ring': '0 0 0 2px #0070cc',
        'ps-focus': '0 0 0 2px #0070cc, 0 0 0 4px rgba(0, 112, 204, 0.3)',
      },
    },
  },
  plugins: [],
};
