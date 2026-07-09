# Event Screenshot Coordinator backend

FastAPI and PostgreSQL backend for turning event screenshots into editable event pages,
sharing them with groups, and collecting RSVP votes.

## Run locally

1. Copy `.env.example` to `.env` and add `OPENAI_API_KEY`.
2. Start PostgreSQL: `docker compose up -d db`.
3. Install: `python -m venv .venv && .venv/bin/pip install -e '.[dev]'`.
4. Migrate: `.venv/bin/alembic upgrade head`.
5. Run: `.venv/bin/uvicorn app.main:app --reload`.

OpenAPI documentation is available at `http://localhost:8000/docs`.

## API flow

1. Upload a screenshot as multipart form data to `POST /api/v1/extractions`, with
   `viewer_timezone` and optional `current_datetime` fields.
2. Present the structured result for review and editing in the React app.
3. Create the reviewed event with `POST /api/v1/events`.
4. Create a group with `POST /api/v1/groups`, then share the event using
   `PUT /api/v1/events/{event_id}/groups/{group_id}`.
5. Upsert a person's RSVP at `PUT /api/v1/events/{event_id}/vote`; read totals from
   the event response or `GET /api/v1/events/{event_id}/votes`.

`created_by` and `voter_id` are external user identifiers. Authentication is deliberately
left behind that boundary so a future auth provider can supply those values instead of trusting
request bodies.
