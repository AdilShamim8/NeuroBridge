import type { Config } from "tailwindcss";
import plugin from "tailwindcss/plugin";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
    "./content/**/*.{md,mdx}"
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "#7F77DD",
          secondary: "#1D9E75",
          ink: "#14131F",
          mist: "#F2F0FF",
          slate: "#5B5C70"
        }
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular"]
      },
      boxShadow: {
        halo: "0 20px 60px -30px rgba(127,119,221,0.55)"
      },
      backgroundImage: {
        "grid-fade": "radial-gradient(circle at 1px 1px, rgba(20,19,31,0.08) 1px, transparent 0)",
        "hero-glow": "radial-gradient(1200px 500px at 30% -20%, rgba(127,119,221,0.25), transparent 60%), radial-gradient(1000px 400px at 90% 10%, rgba(29,158,117,0.2), transparent 60%)"
      }
    }
  },
  plugins: [
    plugin(({ addUtilities }) => {
      addUtilities({
        ".nb-dyslexia": {
          lineHeight: "1.8",
          letterSpacing: "0.05em"
        }
      });
    })
  ]
};

export default config;
