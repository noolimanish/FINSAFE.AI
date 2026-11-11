import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
        display: ["var(--font-jakarta)", "system-ui", "sans-serif"],
      },
      colors: {
        ink: {
          950: "#060B19",
          900: "#0B132B",
          800: "#141E3C",
          700: "#1F2D54",
        },
      },
    },
  },
  plugins: [],
};

export default config;
