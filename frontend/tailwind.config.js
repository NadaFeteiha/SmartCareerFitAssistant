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
          200: '#C7D2FE',
          300: '#A5B4FC',
          400: '#818CF8',
          500: '#6366F1',
          600: '#4F46E5',
          700: '#4338CA',
          800: '#3730A3',
        },
      },
      backgroundImage: {
        'hero-gradient-light':
          'radial-gradient(ellipse at top, rgba(99, 102, 241, 0.10) 0%, rgba(255,255,255,0) 50%)',
        'hero-gradient-dark':
          'radial-gradient(ellipse at top, rgba(99, 102, 241, 0.18) 0%, rgba(10, 15, 28, 0) 50%)',
      },
      boxShadow: {
        soft: '0 1px 2px 0 rgb(15 23 42 / 0.04), 0 1px 3px 0 rgb(15 23 42 / 0.06)',
      },
    },
  },
  plugins: [],
}
