import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx}",
    "./src/components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        "bg-main": "#0a0a0f",
        "bg-card": "#13131a",
        "bg-hover": "#1a1a24",
        "border-subtle": "rgba(255,255,255,0.06)",
        "text-primary": "#f0f0f5",
        "text-muted": "#6b7280",
        "accent-blue": "#3b82f6",
        "accent-green": "#22c55e",
        "accent-red": "#ef4444",
        "accent-yellow": "#eab308",
        "accent-purple": "#a855f7",
      },
    },
  },
  plugins: [],
};
export default config;
