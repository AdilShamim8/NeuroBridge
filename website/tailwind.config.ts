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
          // Darkened from #7F77DD / #1D9E75 so white text on these colors
          // meets WCAG AA (4.5:1) - verified by the axe audit; the originals
          // measured 3.76:1 and 3.39:1.
          primary: "#7169C4",
          secondary: "#188462",
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
