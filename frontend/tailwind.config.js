import defaultTheme from "tailwindcss/defaultTheme";

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["DM Sans", ...defaultTheme.fontFamily.sans],
        display: ["Outfit", "DM Sans", ...defaultTheme.fontFamily.sans],
      },
      colors: {
        tartan: {
          DEFAULT: "#A6192E",
          dark: "#7D1325",
          ink: "#0f172a",
        },
      },
      boxShadow: {
        soft: "0 4px 24px -4px rgba(15, 23, 42, 0.08), 0 2px 10px -2px rgba(15, 23, 42, 0.04)",
        lift: "0 20px 50px -12px rgba(15, 23, 42, 0.14), 0 8px 24px -8px rgba(166, 25, 46, 0.1)",
        glow: "0 0 40px -8px rgba(166, 25, 46, 0.25)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "0%": { backgroundPosition: "200% 0" },
          "100%": { backgroundPosition: "-200% 0" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.5s ease-out both",
        "fade-up-delay": "fade-up 0.55s ease-out 0.08s both",
        shimmer: "shimmer 8s ease-in-out infinite",
      },
      backgroundImage: {
        "mesh-page":
          "radial-gradient(ellipse 100% 70% at 50% -25%, rgba(166, 25, 46, 0.14), transparent 50%), radial-gradient(ellipse 55% 45% at 100% 0%, rgba(37, 99, 235, 0.09), transparent 45%), radial-gradient(ellipse 50% 40% at 0% 100%, rgba(5, 150, 105, 0.08), transparent 48%)",
      },
    },
  },
  plugins: [],
};
