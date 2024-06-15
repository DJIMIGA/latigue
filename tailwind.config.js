/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ['selector', '.dark'],
  content: [
  "./templates/**/*.html",
  "./portfolio/templates/**/*.html",
  "./blog/templates/**/*.html",],
  theme: {
    extend: {},
    screens: {
      '.custom': 'min-width: 400px',
    },
  },
}
