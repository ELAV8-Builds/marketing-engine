import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/app/**/*.{js,ts,jsx,tsx}",
    "./src/components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        surface: {
          0: "#06060b",
          1: "#0d0d14",
          2: "#111118",
          3: "#16161f",
          4: "#1c1c28",
        },
        // Keep old aliases for compatibility
        "bg-main": "#06060b",
        "bg-card": "#111118",
        "bg-hover": "#1c1c28",
        "border-subtle": "rgba(255,255,255,0.07)",
        "text-primary": "#e4e4ec",
        "text-muted": "#6b7280",
        // Accent palette
        "accent-blue": "#3b82f6",
        "accent-green": "#22c55e",
        "accent-red": "#ef4444",
        "accent-yellow": "#eab308",
        "accent-purple": "#7c5cfc",
        "accent-teal": "#5eead4",
        "accent-orange": "#fb923c",
        "accent-pink": "#ec4899",
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-in-right': 'slideInRight 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideInRight: {
          '0%': { opacity: '0', transform: 'translateX(10px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
      },
    },
  },
  plugins: [],
};
export default config;
