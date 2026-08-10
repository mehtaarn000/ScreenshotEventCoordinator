import { ArrowUpRight, MapPin, Users } from "lucide-react";
import Link from "next/link";
import { eventDateParts } from "../lib/format";
import { EventRecord } from "../lib/types";

export function EventCard({ event }: { event: EventRecord }) {
  const date = eventDateParts(event);
  const responses = event.vote_totals.going + event.vote_totals.maybe + event.vote_totals.no;
  return (
    <Link className="event-card" href={`/events/${event.id}`}>
      <div className="date-tile"><span>{date.month}</span><strong>{date.day}</strong></div>
      <div className="event-card-copy">
        <span className="event-kicker">{date.weekday} · {date.time}</span>
        <h3>{event.title}</h3>
        <div className="event-meta">
          {event.location && <span><MapPin size={14} />{event.location}</span>}
          <span><Users size={14} />{responses ? `${responses} responded` : "Waiting on RSVPs"}</span>
        </div>
      </div>
      <ArrowUpRight className="event-arrow" size={20} aria-hidden="true" />
    </Link>
  );
}
