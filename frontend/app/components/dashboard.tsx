"use client";

import { ArrowRight, CalendarDays, Copy, ImagePlus, Link2, Plus, Sparkles, Users, X } from "lucide-react";
import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";
import { apiFetch } from "../lib/api";
import { EventRecord, GroupRecord } from "../lib/types";
import { AppShell } from "./app-shell";
import { EventCard } from "./event-card";
import { useAuth } from "./auth-provider";

type GroupAction = "create" | "join" | null;

export function Dashboard() {
  const { user } = useAuth();
  const [events, setEvents] = useState<EventRecord[]>([]);
  const [groups, setGroups] = useState<GroupRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [action, setAction] = useState<GroupAction>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => { if (action) dialog.current?.showModal(); }, [action]);
  const [value, setValue] = useState("");
  const [saving, setSaving] = useState(false);
  const [copied, setCopied] = useState<string | null>(null);

  const [now] = useState(() => Date.now());

  useEffect(() => {
    let active = true;
    void Promise.all([
      apiFetch<EventRecord[]>("/events"),
      apiFetch<GroupRecord[]>("/groups"),
    ]).then(([nextEvents, nextGroups]) => {
      if (!active) return;
      setEvents(nextEvents);
      setGroups(nextGroups);
      setError(null);
    }).catch((requestError: unknown) => {
      if (active) setError(requestError instanceof Error ? requestError.message : "We couldn’t load your plans.");
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, []);

  async function submitGroup(event: FormEvent) {
    event.preventDefault();
    if (!action || !value.trim()) return;
    setSaving(true);
    try {
      const group = action === "create"
        ? await apiFetch<GroupRecord>("/groups", { method: "POST", body: JSON.stringify({ name: value.trim() }) })
        : await apiFetch<GroupRecord>(`/groups/join/${encodeURIComponent(value.trim())}`, { method: "POST" });
      setGroups((current) => [...current.filter((item) => item.id !== group.id), group].sort((a, b) => a.name.localeCompare(b.name)));
      setAction(null);
      setValue("");
      setError(null);
      if (action === "join") {
        const refreshed = await apiFetch<EventRecord[]>("/events");
        setEvents(refreshed);
      }
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "That group couldn’t be saved.");
    } finally {
      setSaving(false);
    }
  }

  async function copyInvite(group: GroupRecord) {
    try {
      await navigator.clipboard.writeText(`${window.location.origin}/join/${encodeURIComponent(group.invite_code)}`);
      setCopied(group.id);
      window.setTimeout(() => setCopied(null), 1600);
    } catch { setError(`Copy failed. Invite code: ${group.invite_code}`); }
  }

  const upcoming = events.filter((event) => new Date(event.ends_at ?? event.starts_at).getTime() >= now);
  const firstName = user?.user_metadata?.full_name?.split(" ")[0] || user?.email?.split("@")[0] || "there";

  return (
    <AppShell>
      <section className="dashboard-heading">
        <div><div className="eyebrow"><Sparkles size={15} /> Your plans, organized</div><h1>Hey {firstName}, what’s happening?</h1></div>
        <p>{upcoming.length ? `${upcoming.length} upcoming ${upcoming.length === 1 ? "plan" : "plans"} across ${groups.length} ${groups.length === 1 ? "group" : "groups"}.` : "A screenshot is all it takes to get a plan moving."}</p>
      </section>

      {error && <div className="notice notice-error dashboard-notice" role="alert">{error}</div>}

      <section className="quick-add-card">
        <div className="quick-illustration" aria-hidden="true">
          <div className="mini-shot"><span /><span /><span /></div>
          <div className="spark spark-one">✦</div><div className="spark spark-two">✦</div>
        </div>
        <div className="quick-copy">
          <span className="eyebrow"><ImagePlus size={15} /> Add from screenshot</span>
          <h2>Got a concert, dinner, or game in your camera roll?</h2>
          <p>Drop it in. We’ll find the useful bits and make it shareable.</p>
        </div>
        <Link href="/create" className="button button-primary">Choose screenshot <ArrowRight size={17} /></Link>
      </section>

      <div className="dashboard-grid">
        <section className="panel-section" aria-labelledby="upcoming-title">
          <div className="section-title"><div><span>Coming up</span><h2 id="upcoming-title">On the calendar</h2></div><Link href="/create"><Plus size={16} /> New event</Link></div>
          {loading ? <div className="card-loading"><i /><i /><i /></div> : upcoming.length ? (
            <div className="event-list">{upcoming.map((event) => <EventCard event={event} key={event.id} />)}</div>
          ) : (
            <div className="inline-empty"><CalendarDays /><h3>No plans yet</h3><p>Upload the screenshot you keep meaning to send everyone.</p></div>
          )}
        </section>

        <aside className="groups-panel" aria-labelledby="groups-title">
          <div className="section-title"><div><span>Your circles</span><h2 id="groups-title">Groups</h2></div><button type="button" onClick={() => setAction("create")}><Plus size={16} /> New</button></div>
          <div className="group-actions">
            <button type="button" onClick={() => setAction("join")}><Link2 size={17} /><span><strong>Have an invite code?</strong><small>Join your people</small></span><ArrowRight size={16} /></button>
          </div>
          <div className="group-list">
            {groups.map((group, index) => (
              <article className="group-card" key={group.id}>
                <div className={`group-avatar tone-${index % 3}`}><Users size={18} /></div>
                <div><h3>{group.name}</h3><p>{group.role === "owner" ? "You organize this group" : "You’re a member"}</p></div>
                <button type="button" title="Copy invite code" aria-label={`Copy invite code for ${group.name}`} onClick={() => void copyInvite(group)}>{copied === group.id ? "Copied" : <Copy size={16} />}</button>
              </article>
            ))}
            {!loading && !groups.length && <div className="groups-empty"><p>Create a group, then share an event with everyone at once.</p><button type="button" onClick={() => setAction("create")}>Create your first group</button></div>}
          </div>
        </aside>
      </div>

      {action && (
        <dialog ref={dialog} onCancel={() => setAction(null)} className="modal-backdrop" aria-labelledby="group-dialog-title">
          <section className="modal-card">
            <button className="modal-close" type="button" onClick={() => setAction(null)} aria-label="Close"><X size={18} /></button>
            <div className="modal-icon">{action === "create" ? <Users /> : <Link2 />}</div>
            <h2 id="group-dialog-title">{action === "create" ? "Create a group" : "Join a group"}</h2>
            <p>{action === "create" ? "Make a home for the people you plan with most." : "Paste the invite code your friend sent you."}</p>
            <form onSubmit={submitGroup} className="stack-form">
              {error && <p role="alert">{error}</p>}
              <label>{action === "create" ? "Group name" : "Invite code"}<input value={value} onChange={(event) => setValue(event.target.value)} placeholder={action === "create" ? "Sunday crew" : "Paste code here"} required /></label>
              <button className="button button-primary button-full" type="submit" disabled={saving}>{saving ? "Saving…" : action === "create" ? "Create group" : "Join group"}</button>
            </form>
          </section>
        </dialog>
      )}
    </AppShell>
  );
}
