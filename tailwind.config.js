/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./app/report/templates/**/*.{html,js}"],
  theme: {
    extend: {
      colors: {
        primary: {
          light: '#60a5fa',
          DEFAULT: '#2563eb',
          dark: '#1d4ed8',
        },
        success: {
          light: '#4ade80',
          DEFAULT: '#16a34a',
          dark: '#15803d',
        },
        danger: {
          light: '#f87171',
          DEFAULT: '#dc2626',
          dark: '#b91c1c',
        },
      },
      backgroundImage: {
        'gradient-primary': 'linear-gradient(135deg, #60a5fa 0%, #2563eb 100%)',
        'gradient-success': 'linear-gradient(135deg, #4ade80 0%, #16a34a 100%)',
        'gradient-danger': 'linear-gradient(135deg, #f87171 0%, #dc2626 100%)',
      },
    },
  },
  plugins: [],
}
