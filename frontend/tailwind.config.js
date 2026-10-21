/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        canvas: '#030404',
        panel: '#111315',
        panel2: '#17191c',
        accent: '#22d3ee',
      },
      boxShadow: {
        panel: '0 20px 60px rgba(0, 0, 0, 0.35)',
      },
    },
  },
  plugins: [],
};
