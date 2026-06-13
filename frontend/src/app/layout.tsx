import type { Metadata } from "next";
import { Inter, JetBrains_Mono } from "next/font/google";
import Link from "next/link";
import { Radar } from "lucide-react";
import { ThemeToggle } from "@/components/theme-toggle";
import "./globals.css";

// Applies the saved theme to <html> before first paint (prevents a flash).
const themeInit = `(function(){try{if(localStorage.getItem('bidsense-theme')==='dark'){document.documentElement.classList.add('dark');}}catch(e){}})();`;

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const jetbrains = JetBrains_Mono({ subsets: ["latin"], variable: "--font-jetbrains" });

export const metadata: Metadata = {
  title: "BidSense — AI Bid & Proposal Response Engine",
  description:
    "Ingest RFPs, extract requirements, match capabilities, score win probability, draft compliant proposals.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable} ${jetbrains.variable}`} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInit }} />
      </head>
      <body className="min-h-screen font-sans antialiased">
        <header className="sticky top-0 z-40 border-b border-accent-500/15 bg-ink-950/75 backdrop-blur-xl">
          <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-6">
            <Link href="/" className="group flex items-center gap-2.5">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[#9dc08b]/35 to-[#609966]/20 ring-1 ring-accent-600/30 transition-shadow group-hover:shadow-[0_0_16px_-2px_rgba(96,153,102,0.35)]">
                <Radar className="h-4.5 w-4.5 text-accent-600" />
              </span>
              <span className="text-[15px] font-semibold tracking-tight text-slate-100">
                BidSense
                <span className="ml-2 rounded-full bg-ink-800 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wider text-slate-400">
                  Bid &amp; Proposal Engine
                </span>
              </span>
            </Link>
            <nav className="flex items-center gap-1 text-sm">
              <Link href="/" className="rounded-md px-3 py-1.5 text-slate-300 hover:bg-ink-800 hover:text-slate-100">
                Workspaces
              </Link>
              <Link href="/validation" className="rounded-md px-3 py-1.5 text-slate-300 hover:bg-ink-800 hover:text-slate-100">
                Validation
              </Link>
              <span className="mx-1 h-5 w-px bg-ink-700/70" />
              <ThemeToggle />
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
      </body>
    </html>
  );
}
