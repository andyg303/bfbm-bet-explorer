/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['DM Sans', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'ui-monospace', 'SFMono-Regular', 'monospace'],
      },
      colors: {
        terminal: {
          bg: '#0b0f1a',
          surface: '#111827',
          raised: '#1a2236',
          overlay: '#1e293b',
        },
      },
      borderRadius: {
        '2xl': '1rem',
        '3xl': '1.5rem',
      },
      boxShadow: {
        'glow-teal': '0 0 20px -5px rgba(20, 184, 166, 0.3)',
        'glow-teal-lg': '0 0 40px -8px rgba(20, 184, 166, 0.25)',
      },
    },
  },
  plugins: [],
}
