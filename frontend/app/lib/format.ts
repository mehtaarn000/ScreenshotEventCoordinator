import type { EventRecord } from "./types";

export function eventDateParts(event: EventRecord) {
  const date = new Date(event.starts_at);
  const month = new Intl.DateTimeFormat("en-US", { month: "short", timeZone: event.timezone }).format(date);
  const day = new Intl.DateTimeFormat("en-US", { day: "numeric", timeZone: event.timezone }).format(date);
  const weekday = new Intl.DateTimeFormat("en-US", { weekday: "long", timeZone: event.timezone }).format(date);
  const time = new Intl.DateTimeFormat("en-US", { hour: "numeric", minute: "2-digit", timeZone: event.timezone }).format(date);
  return { month, day, weekday, time };
}

export function eventDateLine(event: EventRecord) {
  const start = new Date(event.starts_at);
  const date = new Intl.DateTimeFormat("en-US", {
    weekday: "long", month: "long", day: "numeric", timeZone: event.timezone,
  }).format(start);
  const startTime = new Intl.DateTimeFormat("en-US", {
    hour: "numeric", minute: "2-digit", timeZone: event.timezone,
  }).format(start);
  if (!event.ends_at) return `${date} · ${startTime}`;
  const endTime = new Intl.DateTimeFormat("en-US", {
    hour: "numeric", minute: "2-digit", timeZone: event.timezone,
  }).format(new Date(event.ends_at));
  return `${date} · ${startTime}–${endTime}`;
}

function numericParts(date: Date, timeZone: string) {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  }).formatToParts(date);
  return Object.fromEntries(parts.map((part) => [part.type, part.value]));
}

export function dateTimeLocalValue(iso: string | null, timeZone: string) {
  if (!iso) return "";
  const parts = numericParts(new Date(iso), timeZone);
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
}

export function zonedLocalToIso(value: string, timeZone: string) {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/.exec(value);
  if (!match) throw new Error("Enter a complete date and time.");
  const [, year, month, day, hour, minute] = match.map(Number);
  const desiredUtc = Date.UTC(year, month - 1, day, hour, minute);

  const offsetAt = (timestamp: number) => {
    const parts = numericParts(new Date(timestamp), timeZone);
    const displayedAsUtc = Date.UTC(
      Number(parts.year), Number(parts.month) - 1, Number(parts.day),
      Number(parts.hour), Number(parts.minute), Number(parts.second),
    );
    return displayedAsUtc - timestamp;
  };

  let timestamp = desiredUtc - offsetAt(desiredUtc);
  timestamp = desiredUtc - offsetAt(timestamp);
  return new Date(timestamp).toISOString();
}
