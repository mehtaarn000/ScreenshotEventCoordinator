# Event Screenshot Coordinator backend

FastAPI and PostgreSQL backend for turning event screenshots into editable event pages,
sharing them with groups, and collecting RSVP votes.

## Run locally

1. Copy `.env.example` to `.env`, then add `OPENAI_API_KEY` and your `SUPABASE_URL`.
2. Start PostgreSQL: `docker compose up -d db`.
3. Install: `python -m venv .venv && .venv/bin/pip install -e '.[dev]'`.
4. Migrate: `.venv/bin/alembic upgrade head`.
5. Run: `.venv/bin/uvicorn app.main:app --reload`.

OpenAPI documentation is available at `http://localhost:8000/docs`.

## API flow

All application endpoints except `/health` require a Supabase access token:

```http
Authorization: Bearer <supabase-access-token>
```

The React client should authenticate with `@supabase/supabase-js`, read the current session's
access token, and attach it to each FastAPI request. FastAPI verifies asymmetric `ES256` or
`RS256` tokens using your project's JWKS endpoint. Configure an asymmetric signing key in
Supabase; the legacy shared JWT secret is intentionally unsupported.

1. Upload a screenshot as multipart form data to `POST /api/v1/extractions`, with
   `viewer_timezone` and optional `current_datetime` fields.
2. Present the structured result for review and editing in the React app.
3. Create the reviewed event with `POST /api/v1/events`.
4. Create a group with `POST /api/v1/groups`, join one with
   `POST /api/v1/groups/join/{invite_code}`, then share the event using
   `PUT /api/v1/events/{event_id}/groups/{group_id}`.
5. Upsert a person's RSVP at `PUT /api/v1/events/{event_id}/vote`; read totals from
   the event response or `GET /api/v1/events/{event_id}/votes`.

Event ownership and vote identity come only from the verified JWT `sub` claim. Group members can
view and vote on shared events; only event owners can edit or share them. Existing string user IDs
must contain UUID values before running the authentication migration.
