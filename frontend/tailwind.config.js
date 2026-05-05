/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#EEF2FF',
          100: '#E0E7FF',
          300: '#A5B4FC',
          400: '#818CF8',
          500: '#6366F1',
          600: '#4F46E5',
          700: '#4338CA',
        },
      },
      backgroundImage: {
        'hero-gradient': 'linear-gradient(135deg, #0A0F1C 0%, #1a1040 50%, #0A0F1C 100%)',
      },
    },
  },
  plugins: [],
}
