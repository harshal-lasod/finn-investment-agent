import type { Metadata, Viewport } from "next";
import Link from "next/link";
import Copilot from "@/components/Copilot";
import "./globals.css";

export const metadata: Metadata = {
  title: "FINN — Financial Intelligence",
  description: "Mobile-first portfolio intelligence, grounded research, and network exploration.",
  manifest: "/manifest.json"
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  themeColor: "#173d35"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <div className="app-frame">
          <header className="topbar">
            <Link href="/push" className="brand"><span className="brand-mark">F</span> FINN</Link>
            <span className="topbar-label">Investor intelligence <i className="status-dot" /></span>
          </header>
          <main className="page-content">{children}</main>
          <nav className="bottom-nav" aria-label="Main navigation">
            <Link href="/push"><span>◈</span>Push</Link>
            <Link href="/research"><span>⌕</span>Research</Link>
            <Link href="/network"><span>◎</span>Network</Link>
          </nav>
          <Copilot />
        </div>
      </body>
    </html>
  );
}
