import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Robotics Experiment & Diagnostics Platform",
  description: "Ingesta, visualización y diagnóstico de experimentos de EKF-SLAM.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="es" className="h-full antialiased">
      <body className="min-h-full flex flex-col font-sans">{children}</body>
    </html>
  );
}
