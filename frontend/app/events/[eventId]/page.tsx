"use client";

import { ArrowLeft, CalendarDays, Check, Clock3, ExternalLink, LoaderCircle, MapPin, Share2, Sparkles, Users } from "lucide-react";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell } from "../../components/app-shell";
import { useAuth } from "../../components/auth-provider";
import { apiFetch } from "../../lib/api";
import { eventDateLine } from "../../lib/format";
import { EventRecord, GroupRecord, VoteChoice } from "../../lib/types";

const voteLabels: Record<VoteChoice, string> = { going: "Going", maybe: "Maybe", no: "Can’t go" };

export default function EventPage() {
  const { user, loading: authLoading } = useAuth();
  const params = useParams<{ eventId: string }>();
  const search = useSearchParams();
  const [event, setEvent] = useState<EventRecord | null>(null);
  const [groups, setGroups] = useState<GroupRecord[]>([]);
  const [selected, setSelected] = useState<VoteChoice | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [voting, setVoting] = useState<VoteChoice | null>(null);
  const [shareGroup, setShareGroup] = useState("");
  const [sharing, setSharing] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!user || !params.eventId) return;
    let active = true;
    void Promise.all([
      apiFetch<EventRecord>(`/events/${params.eventId}`),
      apiFetch<GroupRecord[]>("/groups"),
    ]).then(([eventData, groupData]) => {
      if (!active) return;
      setEvent(eventData);
      setSelected(eventData.my_vote);
      setGroups(groupData);
    }).catch((requestError: unknown) => {
      if (active) setError(requestError instanceof Error ? requestError.message : "We couldn’t load this event.");
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, [params.eventId, user]);

  async function castVote(choice: VoteChoice) {
    if (!event || voting) return;
    setVoting(choice);
    setError(null);
    try {
      await apiFetch(`/events/${event.id}/vote`, { method: "PUT", body: JSON.stringify({ choice }) });
      const refreshed = await apiFetch<EventRecord>(`/events/${event.id}`);
      setEvent(refreshed);
      setSelected(refreshed.my_vote);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Your RSVP didn’t save.");
    } finally {
      setVoting(null);
    }
  }

  async function share() {
    if (!event || !shareGroup) return;
    setSharing(true);
    try {
      await apiFetch<void>(`/events/${event.id}/groups/${shareGroup}`, { method: "PUT" });
      setEvent({ ...event, group_ids: [...new Set([...event.group_ids, shareGroup])] });
      setShareGroup("");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "This event couldn’t be shared.");
    } finally {
      setSharing(false);
    }
  }

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(window.location.href.split("?")[0]);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1600);
    } catch { setError("Copy failed. You can copy the event URL from your address bar."); }
  }

  if (authLoading) return <div className="loading-page"><LoaderCircle className="spin" />Loading the plan…</div>;
  if (!user) return <div className="loading-page"><p>Sign in to see this event.</p><Link className="button button-primary" href="/">Go to sign in</Link></div>;
  if (loading) return <div className="loading-page"><LoaderCircle className="spin" />Loading the plan…</div>;
  if (!event) return <AppShell><div className="inline-empty event-error"><CalendarDays /><h1>That plan isn’t here.</h1><p>{error ?? "It may not have been shared with you yet."}</p><Link className="button button-secondary" href="/">Back to my plans</Link></div></AppShell>;

  const isOwner = event.owner_id === user.id;
  const sharedGroups = groups.filter((group) => event.group_ids.includes(group.id));
  const availableGroups = groups.filter((group) => !event.group_ids.includes(group.id));
  const totalVotes = event.vote_totals.going + event.vote_totals.maybe + event.vote_totals.no;

  return (
    <AppShell>
      {search.get("share_failed") && <p role="alert" className="notice notice-error">Your event was created, but sharing failed. Use the group controls below to try again.</p>}
      <div className="event-page-head"><Link href="/" className="back-link"><ArrowLeft size={16} /> Back to plans</Link><div><button className="button button-secondary button-small" type="button" onClick={() => void copyLink()}>{copied ? <><Check size={16} /> Copied</> : <><Share2 size={16} /> Share link</>}</button></div></div>
      {error && <div className="notice notice-error event-notice" role="alert">{error}</div>}
      <section className="event-hero">
        <div className="event-hero-art" aria-hidden="true"><span className="hero-date"><small>{new Intl.DateTimeFormat("en-US", { month: "short", timeZone: event.timezone }).format(new Date(event.starts_at))}</small><strong>{new Intl.DateTimeFormat("en-US", { day: "numeric", timeZone: event.timezone }).format(new Date(event.starts_at))}</strong></span><i>✦</i><b /></div>
        <div className="event-hero-copy">
          <div className="eyebrow"><Sparkles size={14} /> {isOwner ? "You made this plan" : "Shared with you"}</div>
          <h1>{event.title}</h1>
          <div className="hero-details">
            <span><CalendarDays size={18} /><strong>{eventDateLine(event)}</strong></span>
            {event.location && <span><MapPin size={18} /><strong>{event.location}</strong></span>}
          </div>
          {sharedGroups.length > 0 && <div className="shared-chips"><Users size={14} /> Shared with {sharedGroups.map((group) => <span key={group.id}>{group.name}</span>)}</div>}
        </div>
      </section>

      <div className="event-detail-grid">
        <section className="event-body">
          <div className="detail-section"><span className="section-label">The details</span><h2>What’s happening</h2>{event.description ? <p className="description-text">{event.description}</p> : <p className="muted-text">No extra details were added for this event.</p>}</div>
          <div className="info-cards">
            <article><span><Clock3 /></span><div><small>When</small><strong>{eventDateLine(event)}</strong><p>{event.timezone.replaceAll("_", " ")}</p></div></article>
            <article><span><MapPin /></span><div><small>Where</small><strong>{event.location ?? "Location to be decided"}</strong>{event.location && <a href={`https://maps.google.com/?q=${encodeURIComponent(event.location)}`} target="_blank" rel="noreferrer">Open in Maps <ExternalLink size={12} /></a>}</div></article>
          </div>
          {isOwner && availableGroups.length > 0 && <div className="share-panel"><div><span className="section-label">Bring people in</span><h2>Share with another group</h2><p>Everyone in the group will see this event in their plans.</p></div><div className="share-control"><select aria-label="Group to share with" value={shareGroup} onChange={(change) => setShareGroup(change.target.value)}><option value="">Choose a group</option>{availableGroups.map((group) => <option key={group.id} value={group.id}>{group.name}</option>)}</select><button type="button" className="button button-primary" disabled={!shareGroup || sharing} onClick={() => void share()}>{sharing ? "Sharing…" : "Share event"}</button></div></div>}
        </section>

        <aside className="rsvp-card">
          <div className="rsvp-heading"><span className="eyebrow"><Users size={14} /> Quick RSVP</span><h2>Are you in?</h2><p>Your answer helps the group make the call.</p></div>
          <div className="vote-options">
            {(["going", "maybe", "no"] as VoteChoice[]).map((choice) => (
              <button type="button" className={`${choice} ${selected === choice ? "selected" : ""}`} onClick={() => void castVote(choice)} disabled={Boolean(voting)} key={choice}>
                <span>{choice === "going" ? "✓" : choice === "maybe" ? "?" : "×"}</span><strong>{voteLabels[choice]}</strong><b>{event.vote_totals[choice]}</b>
              </button>
            ))}
          </div>
          <div className="vote-summary"><strong>{totalVotes}</strong><span>{totalVotes === 1 ? "person has" : "people have"} responded</span></div>
        </aside>
      </div>
    </AppShell>
  );
}
