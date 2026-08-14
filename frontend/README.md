# Gatherly frontend

React frontend for uploading an event screenshot, reviewing the extracted details, sharing
events with groups, and collecting RSVPs. It uses Supabase Auth in the browser and sends the
session access token to the FastAPI backend.

## Setup

1. Copy `.env.example` to `.env.local`.
2. Add the Supabase project URL and publishable key.
3. Keep `NEXT_PUBLIC_API_URL=http://localhost:8000` for local development.
4. Run `npm install`, then `npm run dev`.

The frontend is available at `http://localhost:3000`.

Never put a Supabase secret or service-role key in a `NEXT_PUBLIC_*` variable. Only the
publishable key belongs in browser configuration.
