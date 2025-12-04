import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Debate Arena",
  description: "Watch AI agents debate any topic from multiple perspectives",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-arena-bg text-white antialiased font-sans">
        {children}
      </body>
    </html>
  );
}
