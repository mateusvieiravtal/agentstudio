/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        agent: {
          idle: "#cbd5e1",
          running: "#3b82f6",
          done: "#22c55e",
          failed: "#ef4444",
          paused: "#f59e0b",
        },
      },
    },
  },
  plugins: [],
};
