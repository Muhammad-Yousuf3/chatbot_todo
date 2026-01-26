import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Primary accent - Midnight AI Glass gradient (blue to purple)
        primary: {
          50: '#eef4ff',
          100: '#dce8ff',
          200: '#b9d1ff',
          300: '#8bb4ff',
          400: '#5B8CFF', // Gradient start - accent blue
          500: '#7B6CF6', // Midpoint
          600: '#8B5CF6', // Gradient end - accent purple
          700: '#7c3aed',
          800: '#6d28d9',
          900: '#5b21b6',
          950: '#4c1d95',
        },
        // Success - Fresh green (spec: #22C55E)
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22C55E', // Spec color
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        // Error - Danger red (spec: #EF4444)
        error: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#EF4444', // Spec color
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        },
        // Warning - Amber (spec: #FACC15)
        warning: {
          50: '#fefce8',
          100: '#fef9c3',
          200: '#fef08a',
          300: '#fde047',
          400: '#facc15',
          500: '#FACC15', // Spec color
          600: '#ca8a04',
          700: '#a16207',
          800: '#854d0e',
          900: '#713f12',
        },
        // Dark mode - Midnight AI Glass palette
        dark: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#232D42', // Borders/inputs
          700: '#1A2235', // Elevated surface
          800: '#12182B', // Surface/cards
          900: '#0B0F1A', // Background
          950: '#050810',
        },
      },
      fontFamily: {
        sans: ['var(--font-plus-jakarta)', 'Plus Jakarta Sans', 'system-ui', '-apple-system', 'sans-serif'],
      },
      boxShadow: {
        'glow': '0 0 20px -5px rgba(91, 140, 255, 0.4)',
        'glow-lg': '0 0 30px -5px rgba(91, 140, 255, 0.5)',
        'glow-accent': '0 0 20px -5px rgba(139, 92, 246, 0.5)',
        'glass': '0 4px 30px rgba(0, 0, 0, 0.3), inset 0 0 0 1px rgba(91, 140, 255, 0.1)',
        'glass-hover': '0 8px 40px rgba(91, 140, 255, 0.2), inset 0 0 0 1px rgba(91, 140, 255, 0.2)',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-subtle': 'pulseSubtle 2s ease-in-out infinite',
        'typing-bounce': 'typingBounce 1.4s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseSubtle: {
          '0%, 100%': { opacity: '1' },
          '50%': { opacity: '0.7' },
        },
        typingBounce: {
          '0%, 60%, 100%': { transform: 'translateY(0)' },
          '30%': { transform: 'translateY(-4px)' },
        },
      },
    },
  },
  plugins: [],
}
export default config
