"use client";

import { ArrowRight, CalendarDays, ImagePlus, Sparkles } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "./components/auth-provider";
import { Dashboard } from "./components/dashboard";

function AuthScreen() {
  const { signIn, signUp, configured } = useAuth();
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setMessage(null);
    try {
      const result = mode === "signin" ? await signIn(email, password) : await signUp(email, password);
      if (result) setMessage(result);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Something went wrong. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-story" aria-labelledby="auth-heading">
        <div className="brand brand-light"><span className="brand-mark"><CalendarDays /></span> Gatherly</div>
        <div className="auth-story-content">
          <div className="eyebrow light"><Sparkles size={15} /> Plans, without the planning</div>
          <h1 id="auth-heading">Turn any event screenshot into a plan everyone can join.</h1>
          <p>Upload the screenshot. We’ll pull out the details. Your people can vote in one tap.</p>
          <div className="story-flow" aria-label="How Gatherly works">
            <div><span>1</span><ImagePlus /><strong>Drop a screenshot</strong></div>
            <i />
            <div><span>2</span><Sparkles /><strong>Check the details</strong></div>
            <i />
            <div><span>3</span><CalendarDays /><strong>Share & decide</strong></div>
          </div>
        </div>
        <p className="auth-note">Less group-chat archaeology. More showing up.</p>
      </section>

      <section className="auth-panel">
        <div className="auth-card">
          <div className="mobile-brand brand"><span className="brand-mark"><CalendarDays /></span> Gatherly</div>
          <div className="auth-tabs" role="tablist" aria-label="Authentication mode">
            <button className={mode === "signin" ? "active" : ""} onClick={() => setMode("signin")} type="button">Sign in</button>
            <button className={mode === "signup" ? "active" : ""} onClick={() => setMode("signup")} type="button">Create account</button>
          </div>
          <h2>{mode === "signin" ? "Welcome back" : "Make plans happen"}</h2>
          <p>{mode === "signin" ? "Sign in to see what’s coming up." : "Start turning screenshots into shared plans."}</p>
          <form onSubmit={submit} className="stack-form">
            <label>Email address<input type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" required /></label>
            <label>Password<input type="password" autoComplete={mode === "signin" ? "current-password" : "new-password"} value={password} onChange={(event) => setPassword(event.target.value)} placeholder="At least 8 characters" minLength={8} required /></label>
            <button className="button button-primary button-full" disabled={busy || !configured} type="submit">
              {busy ? "One moment…" : mode === "signin" ? "Sign in" : "Create account"}<ArrowRight size={17} />
            </button>
          </form>
          {!configured && <div className="notice notice-error" role="alert">Add the Supabase public URL and publishable key to the frontend environment.</div>}
          {message && <div className="notice" role="status">{message}</div>}
          <p className="fine-print">By continuing, you agree to keep the group chat peaceful.</p>
        </div>
      </section>
    </main>
  );
}

export default function Home() {
  const { user, loading } = useAuth();
  const router = useRouter();
  const search = useSearchParams();
  const next = search.get("next");
  useEffect(() => {
    if (user && next && /^\/(?:events\/|join\/|create$)/.test(next) && !next.includes("\\")) router.replace(next);
  }, [user, next, router]);
  if (loading) return <div className="loading-page"><span className="brand-mark"><CalendarDays /></span><span>Gathering your plans…</span></div>;
  return user ? <Dashboard /> : <AuthScreen />;
}
