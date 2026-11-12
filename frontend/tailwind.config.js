/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        sidebar: "#075477",
        accent: "#16B6B0",
        canvas: "#EFF9FA",
        ink: "#16354A",
        muted: "#738A98",
        border: "#DCECEF",
      },
    },
  },
  plugins: [],
};
