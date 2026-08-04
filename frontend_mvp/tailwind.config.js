/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // "ink" stays the name used throughout existing components, now
        // mapped to the modern slate primary instead of pure black.
        ink: '#1E293B',
        soft: '#64748B',
        faint: '#94A3B8',
        canvas: '#F8FAFC',
        panel: '#F1F5F9',
        placeholder: '#E2E8F0',
        indigo: {
          DEFAULT: '#3B82F6',
          dark: '#2563EB',
        },
        amber: {
          DEFAULT: '#F59E0B',
          dark: '#D97706',
        },
        coral: {
          DEFAULT: '#EF4444',
          dark: '#DC2626',
        },
      },
      fontFamily: {
        display: ['"Space Grotesk"', 'sans-serif'],
        sans: ['Inter', 'Helvetica Neue', 'Arial', 'sans-serif'],
        mono: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        sm: '6px',
        DEFAULT: '8px',
        lg: '12px',
        xl: '16px',
      },
      opacity: {
        8: '0.08',
        12: '0.15',
        15: '0.15',
        45: '0.45',
      },
      boxShadow: {
        card: '0 1px 2px rgba(30, 41, 59, 0.04), 0 8px 24px -12px rgba(30, 41, 59, 0.12)',
        'card-hover': '0 4px 10px rgba(30, 41, 59, 0.08), 0 18px 34px -14px rgba(30, 41, 59, 0.22)',
        pop: '0 20px 50px -12px rgba(30, 41, 59, 0.3)',
      },
      keyframes: {
        'fade-slide-in': {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'toast-in': {
          '0%': { opacity: '0', transform: 'translateY(-8px) scale(0.98)' },
          '100%': { opacity: '1', transform: 'translateY(0) scale(1)' },
        },
        'drawer-in': {
          '0%': { transform: 'translateX(-100%)' },
          '100%': { transform: 'translateX(0)' },
        },
      },
      animation: {
        'fade-slide-in': 'fade-slide-in 0.3s ease both',
        'toast-in': 'toast-in 0.25s ease both',
      },
    },
  },
  plugins: [],
}
