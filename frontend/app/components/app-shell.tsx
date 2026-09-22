"use client";

import { CalendarDays, LogOut, Plus } from "lucide-react";
import Link from "next/link";
import { ReactNode, useState } from "react";
import { useAuth } from "./auth-provider";

export function AppShell({ children }: { children: ReactNode }) {
  const { user, signOut } = useAuth();
  const [error, setError] = useState("");
  async function logout() {
    try { await signOut(); }
    catch { setError("Sign out failed. Please try again."); }
  }
  return (
    <div className="app-page">
      <header className="topbar">
        <Link href="/" className="brand"><span className="brand-mark"><CalendarDays /></span> Gatherly</Link>
        <nav aria-label="Main navigation">
          <Link href="/" className="nav-link">My plans</Link>
          <Link href="/create" className="button button-primary button-small"><Plus size={16} /> Add event</Link>
          <button type="button" className="avatar-button" onClick={() => void logout()} title="Sign out" aria-label={`Sign out ${user?.email ?? ""}`}>
            <span>{user?.email?.slice(0, 1).toUpperCase() ?? "U"}</span><LogOut size={16} />
          </button>
        </nav>
      </header>
      <main className="main-content">{error && <p role="alert">{error}</p>}{children}</main>
    </div>
  );
}
