import type { Config } from "tailwindcss";

export default <Partial<Config>>{
  theme: {
    extend: {
      colors: {
        ink: "#172033",
        sand: "#f8f3eb",
        clay: "#f07f4f",
        pine: "#1e7f74",
        mist: "#dce5e4"
      },
      boxShadow: {
        soft: "0 18px 40px rgba(23, 32, 51, 0.08)"
      },
      fontFamily: {
        sans: ["Manrope", "ui-sans-serif", "system-ui"],
        display: ["Space Grotesk", "ui-sans-serif", "system-ui"]
      }
    }
  }
};

