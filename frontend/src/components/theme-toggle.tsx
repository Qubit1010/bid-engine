"use client";

import { useEffect, useState } from "react";
import { Moon, Sun } from "lucide-react";

/**
 * Light/dark switch. The initial <html class="dark"> is applied by the inline
 * script in layout.tsx before paint (no FOUC); this button just flips it and
 * persists the choice to localStorage.
 */
export function ThemeToggle() {
  const [mounted, setMounted] = useState(false);
  const [dark, setDark] = useState(false);

  useEffect(() => {
    setDark(document.documentElement.classList.contains("dark"));
    setMounted(true);
  }, []);

  const toggle = () => {
    const next = !dark;
    setDark(next);
    document.documentElement.classList.toggle("dark", next);
    try {
      localStorage.setItem("bidsense-theme", next ? "dark" : "light");
    } catch {}
  };

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={dark ? "Switch to light theme" : "Switch to dark theme"}
      title={dark ? "Light mode" : "Dark mode"}
      className="flex h-8 w-8 cursor-pointer items-center justify-center rounded-md border border-ink-700/70 text-slate-400 transition-colors hover:border-accent-500/40 hover:bg-ink-800 hover:text-accent-400"
    >
      {/* Render a stable icon until mounted to avoid a hydration mismatch */}
      {mounted && dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
    </button>
  );
}
