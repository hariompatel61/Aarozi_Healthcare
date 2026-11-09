/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./components/**/*.{js,vue,ts}",
    "./layouts/**/*.vue",
    "./pages/**/*.vue",
    "./plugins/**/*.{js,ts}",
    "./app.vue",
    "./error.vue"
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        navy: {
          50: '#f0f4f8',
          100: '#d9e2ec',
          200: '#bcccdc',
          800: '#102a43',
          900: '#0b1d30',
        },
        clinical: {
          teal: '#0d9488',
          dark: '#0f172a',
          surface: '#f8fafc',
          border: '#e2e8f0',
        }
      }
    },
  },
  plugins: [],
}
