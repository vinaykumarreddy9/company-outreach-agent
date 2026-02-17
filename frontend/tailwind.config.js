/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#1e1b4b', // Deep Indigo / Midnight Blue
          light: '#312e81',
          foreground: '#ffffff',
        },
        secondary: {
          DEFAULT: '#8b5cf6', // Electric Violet
          light: '#a78bfa',
          foreground: '#ffffff',
        },
        accent: {
          DEFAULT: '#06b6d4', // Neon Cyan
          light: '#22d3ee',
          foreground: '#ffffff',
        },
        background: '#f8fafc', // Light slate
        surface: '#ffffff',
        border: '#e2e8f0', // Soft gray
        text: {
          primary: '#0f172a',
          secondary: '#475569',
          muted: '#94a3b8',
        }
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['Plus Jakarta Sans', 'Inter', 'sans-serif'],
      },
      borderRadius: {
        lg: '0.5rem',
        xl: '0.75rem',
        '2xl': '1rem',
      },
      boxShadow: {
        'soft': '0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03)',
        'medium': '0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -2px rgba(0, 0, 0, 0.04)',
        'glow': '0 0 15px rgba(139, 92, 246, 0.3)',
      }
    },
  },
  plugins: [],
}
