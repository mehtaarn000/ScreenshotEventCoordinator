"use client";
/* eslint-disable @next/next/no-img-element -- previews are user-selected object URLs */

import { AlertCircle, ArrowLeft, ArrowRight, CalendarDays, Check, ImagePlus, LoaderCircle, MapPin, Sparkles, Upload, Users } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ChangeEvent, DragEvent, FormEvent, useEffect, useRef, useState } from "react";
import { AppShell } from "../components/app-shell";
import { useAuth } from "../components/auth-provider";
import { apiFetch } from "../lib/api";
import { dateTimeLocalValue, zonedLocalToIso } from "../lib/format";
import { EventRecord, ExtractionResult, GroupRecord } from "../lib/types";

const MAX_FILE_SIZE = 10 * 1024 * 1024;
const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp", "image/gif"];

interface EventForm {
  title: string;
  startsAt: string;
  endsAt: string;
  timezone: string;
  location: string;
  description: string;
}

export default function CreateEventPage() {
  const { user, loading: authLoading } = useAuth();
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement>(null);
  const previewRef = useRef<string | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [stage, setStage] = useState<"upload" | "extracting" | "review">("upload");
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ExtractionResult | null>(null);
  const [form, setForm] = useState<EventForm | null>(null);
  const [groups, setGroups] = useState<GroupRecord[]>([]);
  const [groupId, setGroupId] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => () => {
    if (previewRef.current) URL.revokeObjectURL(previewRef.current);
  }, []);

  useEffect(() => {
    if (!user) return;
    let active = true;
    void apiFetch<GroupRecord[]>("/groups").then((data) => {
      if (active) setGroups(data);
    }).catch(() => undefined);
    return () => { active = false; };
  }, [user]);

  function chooseFile(nextFile?: File) {
    if (!nextFile) return;
    if (!ACCEPTED_TYPES.includes(nextFile.type)) {
      setError("Choose a PNG, JPEG, WebP, or GIF screenshot.");
      return;
    }
    if (nextFile.size > MAX_FILE_SIZE) {
      setError("That screenshot is over 10 MB. Try a smaller image.");
      return;
    }
    if (previewRef.current) URL.revokeObjectURL(previewRef.current);
    const url = URL.createObjectURL(nextFile);
    previewRef.current = url;
    setPreview(url);
    setFile(nextFile);
    setError(null);
  }

  function onInput(event: ChangeEvent<HTMLInputElement>) {
    chooseFile(event.target.files?.[0]);
  }

  function onDrop(event: DragEvent<HTMLLabelElement>) {
    event.preventDefault();
    setDragging(false);
    chooseFile(event.dataTransfer.files[0]);
  }

  async function extract() {
    if (!file) return;
    setStage("extracting");
    setError(null);
    const data = new FormData();
    data.set("screenshot", file);
    data.set("viewer_timezone", Intl.DateTimeFormat().resolvedOptions().timeZone);
    data.set("current_datetime", new Date().toISOString());
    try {
      const extraction = await apiFetch<ExtractionResult>("/extractions", { method: "POST", body: data });
      setResult(extraction);
      setForm({
        title: extraction.title,
        startsAt: dateTimeLocalValue(extraction.starts_at, extraction.timezone),
        endsAt: dateTimeLocalValue(extraction.ends_at, extraction.timezone),
        timezone: extraction.timezone,
        location: extraction.location ?? "",
        description: extraction.description ?? "",
      });
      setStage("review");
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "We couldn’t read that screenshot.");
      setStage("upload");
    }
  }

  function update(field: keyof EventForm, value: string) {
    setForm((current) => current ? { ...current, [field]: value } : current);
  }

  async function createEvent(event: FormEvent) {
    event.preventDefault();
    if (!form) return;
    setSaving(true);
    setError(null);
    try {
      const created = await apiFetch<EventRecord>("/events", {
        method: "POST",
        body: JSON.stringify({
          title: form.title,
          starts_at: zonedLocalToIso(form.startsAt, form.timezone),
          ends_at: form.endsAt ? zonedLocalToIso(form.endsAt, form.timezone) : null,
          timezone: form.timezone,
          location: form.location || null,
          description: form.description || null,
        }),
      });
      if (groupId) await apiFetch<void>(`/events/${created.id}/groups/${groupId}`, { method: "PUT" });
      router.push(`/events/${created.id}?created=1`);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "The event couldn’t be created.");
      setSaving(false);
    }
  }

  if (authLoading) return <div className="loading-page"><LoaderCircle className="spin" />Loading…</div>;
  if (!user) return <div className="loading-page"><p>Sign in to add an event.</p><Link className="button button-primary" href="/">Go to sign in</Link></div>;

  return (
    <AppShell>
      <div className="create-head">
        <Link href="/" className="back-link"><ArrowLeft size={16} /> Back to plans</Link>
        <div className="step-indicator" aria-label={`Step ${stage === "review" ? 2 : 1} of 2`}>
          <span className="active"><i>1</i> Upload</span><b /><span className={stage === "review" ? "active" : ""}><i>2</i> Review</span>
        </div>
      </div>

      {stage !== "review" ? (
        <section className="upload-layout">
          <div className="upload-copy">
            <div className="eyebrow"><Sparkles size={15} /> Screenshot to event</div>
            <h1>Drop the screenshot.<br />Keep the plan.</h1>
            <p>We’ll pull out the title, date, time, place, and details. You get the final say before anything is shared.</p>
            <ul><li><Check /> Review every detail</li><li><Check /> Your screenshot isn’t stored</li><li><Check /> Share only when you’re ready</li></ul>
          </div>

          <div className="upload-card">
            {stage === "extracting" ? (
              <div className="extracting-state" role="status">
                {preview && <img src={preview} alt="Event screenshot being analyzed" />}
                <div className="scan-line" />
                <div className="extracting-copy"><span><Sparkles size={17} /></span><div><strong>Finding the important bits…</strong><small>Reading dates, places, and event details</small></div></div>
              </div>
            ) : (
              <>
                <label className={`upload-dropzone ${dragging ? "dragging" : ""} ${preview ? "has-preview" : ""}`} onDragEnter={() => setDragging(true)} onDragLeave={() => setDragging(false)} onDragOver={(event) => event.preventDefault()} onDrop={onDrop}>
                  <input ref={inputRef} type="file" accept={ACCEPTED_TYPES.join(",")} onChange={onInput} />
                  {preview ? <><img src={preview} alt="Selected event screenshot" /><span className="replace-image"><ImagePlus size={16} /> Choose a different image</span></> : <><span className="upload-icon"><Upload /></span><strong>Drop your screenshot here</strong><p>or click to choose from your device</p><small>PNG, JPEG, WebP, or GIF · up to 10 MB</small></>}
                </label>
                {error && <div className="notice notice-error" role="alert"><AlertCircle size={16} />{error}</div>}
                <button type="button" className="button button-primary button-full" disabled={!file} onClick={() => void extract()}>Extract event details <Sparkles size={17} /></button>
              </>
            )}
          </div>
        </section>
      ) : form && (
        <section className="review-layout">
          <div className="review-main">
            <div className="review-heading"><div><div className="eyebrow"><Check size={15} /> Details found</div><h1>Give everything a quick look.</h1><p>AI is handy. You’re still the expert on where you’re going.</p></div><div className="confidence-pill"><Sparkles size={15} /><span><strong>{Math.round((result?.confidence ?? 0) * 100)}%</strong> confidence</span></div></div>
            {result?.warnings.map((warning) => <div className="notice review-warning" key={warning}><AlertCircle size={16} />{warning}</div>)}
            {error && <div className="notice notice-error" role="alert"><AlertCircle size={16} />{error}</div>}
            <form className="event-form" onSubmit={createEvent}>
              <label className="field-wide"><span>Event title</span><input value={form.title} onChange={(event) => update("title", event.target.value)} required maxLength={200} /></label>
              <label><span><CalendarDays size={15} /> Starts</span><input type="datetime-local" value={form.startsAt} onChange={(event) => update("startsAt", event.target.value)} required /></label>
              <label><span><CalendarDays size={15} /> Ends <small>optional</small></span><input type="datetime-local" value={form.endsAt} onChange={(event) => update("endsAt", event.target.value)} /></label>
              <label className="field-wide"><span>Timezone</span><input value={form.timezone} onChange={(event) => update("timezone", event.target.value)} placeholder="America/New_York" required /></label>
              <label className="field-wide"><span><MapPin size={15} /> Location</span><input value={form.location} onChange={(event) => update("location", event.target.value)} placeholder="Add an address or meeting spot" maxLength={300} /></label>
              <label className="field-wide"><span>Description</span><textarea rows={5} value={form.description} onChange={(event) => update("description", event.target.value)} placeholder="Anything your group should know?" maxLength={5000} /></label>
              <div className="share-field field-wide"><label htmlFor="share-group"><Users size={15} /> Share with a group <small>optional</small></label><select id="share-group" value={groupId} onChange={(event) => setGroupId(event.target.value)}><option value="">Keep it to myself for now</option>{groups.map((group) => <option value={group.id} key={group.id}>{group.name}</option>)}</select></div>
              <div className="form-actions field-wide"><button type="button" className="button button-secondary" onClick={() => setStage("upload")}><ArrowLeft size={16} /> Use another image</button><button type="submit" className="button button-primary" disabled={saving}>{saving ? <><LoaderCircle className="spin" size={17} /> Creating event…</> : <>Create event <ArrowRight size={17} /></>}</button></div>
            </form>
          </div>
          <aside className="review-preview"><span>Original screenshot</span>{preview && <img src={preview} alt="Original event screenshot" />}<p><Sparkles size={14} /> Extracted with AI, reviewed by you.</p></aside>
        </section>
      )}
    </AppShell>
  );
}
