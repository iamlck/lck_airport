/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        aviation: {
          dark: '#080d1a',
          card: '#0f172a',
          cyan: '#00e5ff',
          blue: '#0284c7',
          glow: 'rgba(0, 229, 255, 0.25)'
        }
      }
    },
  },
  plugins: [],
}

