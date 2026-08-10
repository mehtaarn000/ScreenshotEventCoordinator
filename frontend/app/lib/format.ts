import { EventRecord } from "./types";

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
