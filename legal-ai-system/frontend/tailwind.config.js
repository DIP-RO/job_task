/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./pages/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: "#eff6ff",
          500: "#1e40af",
          600: "#1e3a8a",
          700: "#1e40af",
          900: "#0c1e3a",
        },
        secondary: {
          500: "#7c3aed",
          600: "#6d28d9",
          700: "#5b21b6",
        },
        success: {
          500: "#10b981",
          600: "#059669",
        },
        error: {
          500: "#ef4444",
          600: "#dc2626",
        },
        warning: {
          500: "#f59e0b",
          600: "#d97706",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)"],
      },
      spacing: {
        128: "32rem",
      },
    },
  },
  plugins: [],
};
