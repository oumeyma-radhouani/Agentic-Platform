import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "NOVA Agentic CRM",
  description: "Enterprise AI Platform",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased bg-slate-50 text-slate-900 h-screen overflow-hidden">
        {children}
      </body>
    </html>
  );
}