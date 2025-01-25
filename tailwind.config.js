/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./**/*.html",      // Scan all HTML files in the padoject
    "./app/**/*.py",    // Scan Python files (e.g., FastHTML components)
  ],
  theme: {
    extend: {
      colors: {
        "dark-theme-gray": {
          DEFAULT: "#1E1E1E",
        },
        "dark-theme-lightgray": {
          DEFAULT: "#4A4A4A",
        },
      },
    },
  },
  plugins: [],
}

