import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "NOVA - Agentic Platform",
  description: "Agentic Platform UI",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased bg-[#0d1117] text-[#c9d1d9]">
        {children}
      </body>
    </html>
  );
}