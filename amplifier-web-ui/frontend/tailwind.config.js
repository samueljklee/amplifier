/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      /* Amplified Design System Extensions */
      minWidth: {
        'touch': '44px', // Apple Human Interface Guidelines minimum
      },
      minHeight: {
        'touch': '44px', // Apple Human Interface Guidelines minimum
      },
      spacing: {
        // Explicit 8px spacing system for consistency
        'xs': '4px',   // 0.5 in Tailwind (extra small)
        'sm': '8px',   // 2 in Tailwind (small)
        'md': '16px',  // 4 in Tailwind (medium)
        'lg': '24px',  // 6 in Tailwind (large)
        'xl': '32px',  // 8 in Tailwind (extra large)
        '2xl': '48px', // 12 in Tailwind (2x extra large)
      },
      transitionDuration: {
        // Motion protocol durations
        'instant': '50ms',      // <100ms: instant feedback
        'responsive': '200ms',  // 100-300ms: responsive interactions
        'deliberate': '400ms',  // 300-1000ms: deliberate transitions
      },
    },
  },
  plugins: [],
}
