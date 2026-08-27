import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Genera .next/standalone: solo el server.js + los node_modules que
  // realmente se usan en runtime, en vez de copiar todo el proyecto a la
  // imagen de Docker. Reduce el tamaño final de la imagen drásticamente.
  output: "standalone",
};

export default nextConfig;
