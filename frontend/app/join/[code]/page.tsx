"use client";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";
import { useAuth } from "../../components/auth-provider";
import { AppShell } from "../../components/app-shell";
import { apiFetch } from "../../lib/api";

export default function JoinGroup() {
  const { code } = useParams<{ code: string }>();
  const { user, loading } = useAuth();
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function join() {
    setBusy(true);
    try {
      await apiFetch(`/groups/join/${encodeURIComponent(code)}`, { method: "POST" });
      router.push("/");
    } catch (err) { setError(err instanceof Error ? err.message : "Could not join group."); setBusy(false); }
  }
  if (loading) return <p>Loading…</p>;
  if (!user) return <Link href={`/?next=${encodeURIComponent(`/join/${encodeURIComponent(code)}`)}`}>Sign in to accept invitation</Link>;
  return <AppShell><h1>You’re invited</h1><p>Join this group to see its shared plans. Joining shares your membership with the group.</p>
    {error && <p role="alert">{error}</p>}
    <button className="button button-primary" disabled={busy} onClick={() => void join()}>{busy ? "Joining…" : "Join group"}</button>
  </AppShell>;
}
