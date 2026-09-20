"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { AppShell } from "../../../components/app-shell";
import { useAuth } from "../../../components/auth-provider";
import { apiFetch } from "../../../lib/api";
import { dateTimeLocalValue, zonedLocalToIso } from "../../../lib/format";
import type { EventRecord } from "../../../lib/types";

export default function EditEvent() {
  const { eventId } = useParams<{ eventId: string }>();
  const { user, loading } = useAuth();
  const router = useRouter();
  const [event, setEvent] = useState<EventRecord | null>(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  useEffect(() => {
    if (!user) return;
    let active = true;
    void apiFetch<EventRecord>(`/events/${eventId}`).then((value) => {
      if (active) setEvent(value);
    }).catch((err: Error) => { if (active) setError(err.message); });
    return () => { active = false; };
  }, [user, eventId]);

  async function save(change: FormEvent<HTMLFormElement>) {
    change.preventDefault();
    const data = new FormData(change.currentTarget);
    const text = (key: string) => String(data.get(key) ?? "");
    setSaving(true);
    setError("");
    try {
      await apiFetch(`/events/${eventId}`, { method: "PUT", body: JSON.stringify({
        title: text("title"), timezone: text("timezone"),
        starts_at: zonedLocalToIso(text("starts_at"), text("timezone")),
        ends_at: text("ends_at") ? zonedLocalToIso(text("ends_at"), text("timezone")) : null,
        location: text("location") || null, description: text("description") || null,
      }) });
      router.push(`/events/${eventId}`);
    } catch (err) { setError(err instanceof Error ? err.message : "Could not save changes."); }
    finally { setSaving(false); }
  }

  if (loading) return <p className="loading-page">Loading…</p>;
  if (!user) return <Link href={`/?next=${encodeURIComponent(`/events/${eventId}/edit`)}`}>Sign in to edit</Link>;
  return <AppShell><Link href={`/events/${eventId}`}>Back to event</Link><h1>Edit event</h1>
    {error && <p className="notice notice-error" role="alert">{error}</p>}
    {event && event.owner_id !== user.id && <p>Only the organizer can edit this event.</p>}
    {event?.owner_id === user.id && <form onSubmit={save} className="review-form">
      <label>Title<input name="title" required maxLength={200} defaultValue={event.title} /></label>
      <label>Start<input name="starts_at" type="datetime-local" required defaultValue={dateTimeLocalValue(event.starts_at, event.timezone)} /></label>
      <label>End<input name="ends_at" type="datetime-local" defaultValue={dateTimeLocalValue(event.ends_at, event.timezone)} /></label>
      <label>Timezone<input name="timezone" required defaultValue={event.timezone} /></label>
      <p>Dates and times are interpreted in the timezone entered above.</p>
      <label>Location<input name="location" maxLength={300} defaultValue={event.location ?? ""} /></label>
      <label>Description<textarea name="description" maxLength={5000} defaultValue={event.description ?? ""} /></label>
      <button className="button button-primary" disabled={saving}>{saving ? "Saving…" : "Save changes"}</button>
    </form>}
  </AppShell>;
}
