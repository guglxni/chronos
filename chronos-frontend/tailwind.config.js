/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // PlayStation-inspired palette — retained for backward compat
        ps: {
          blue: '#0070cc',
          cyan: '#1eaedb',
          link: '#1883fd',
          dark: '#0068bd',
          darklink: '#53b1ff',
          orange: '#d53b00',
          charcoal: '#1f1f1f',
        },
        // Nike-inspired CHRONOS design system
        chronos: {
          blue: '#5B8AFF',
          black: '#111111',
          gray: '#F5F5F5',
          secondary: '#4A4A4C',
          // Legacy sky-* compat shim
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
        heading: ['"ChunkFive Print"', 'Georgia', 'serif'],
        body: ['"CM Geom"', 'system-ui', 'sans-serif'],
        mono: ['"CM Geom"', 'ui-monospace', 'monospace'],
        display: ['"Inter"', 'system-ui', '-apple-system', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.3s ease-out forwards',
        'shimmer': 'shimmer 1.5s linear infinite',
        'blink': 'blink 1s step-end infinite',
        'slide-up': 'slideUp 0.4s ease-out forwards',
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
        blink: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
      boxShadow: {
        'ps-ring': '0 0 0 2px #0070cc',
        'ps-focus': '0 0 0 2px #0070cc, 0 0 0 4px rgba(0, 112, 204, 0.3)',
      },
    },
  },
  plugins: [],
};
