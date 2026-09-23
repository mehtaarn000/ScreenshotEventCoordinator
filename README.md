# Gatherly

Gatherly turns screenshots of concerts, dinners, games, and other events into plans a group can
actually decide on. A vision-capable model extracts the details, the creator reviews them, and
friends respond Going, Maybe, or No.

## Stack

- React 19 frontend in `frontend/`
- FastAPI backend in `app/`
- PostgreSQL with SQLAlchemy and Alembic
- Supabase Auth with asymmetric JWT verification
- OpenAI Responses API with vision and structured Pydantic output

## Local setup

### 1. Configure Supabase

Create a Supabase project and use an asymmetric signing key. In the project authentication
settings, add `http://localhost:3000` as an allowed site/redirect URL.

Copy the environment examples:

```bash
cp .env.example .env
cp frontend/.env.example frontend/.env.local
```

Set `SUPABASE_URL` and `OPENAI_API_KEY` in `.env`. Set the same Supabase URL plus the project's
publishable key in `frontend/.env.local`. Never expose a secret or service-role key to React.

### 2. Start the API and database

```bash
docker compose up --build
```

PostgreSQL starts first, Alembic applies the schema, and FastAPI becomes available at
`http://localhost:8000`. Interactive API documentation is at `http://localhost:8000/docs`.

### 3. Start React

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`, create an account, and confirm the email if email confirmation is
enabled in Supabase.

## Product flow

1. React authenticates the user with Supabase and attaches the access token to API calls.
2. `POST /api/v1/extractions` accepts a screenshot and returns editable structured event data.
3. `POST /api/v1/events` saves the reviewed event under the authenticated user's UUID.
4. Users create or join groups and event owners share events with those groups.
5. Group members view the event page and upsert their RSVP. The API returns totals and the
   current user's response.

## Useful commands

Backend:

```bash
python -m venv .venv
.venv/bin/pip install -e '.[dev]'
.venv/bin/ruff check .
.venv/bin/pytest
```

Frontend:

```bash
cd frontend
npm run lint
npm run typecheck
npm test
```

Existing pre-authentication `created_by` and `voter_id` values must be UUID strings before the
authentication migration can convert them to Supabase user IDs.

## Event management

Owners can edit or delete events and remove group sharing from the event page. Members can
change or withdraw their RSVP; totals are refreshed from the server after each change.
The dashboard offers past plans as well as upcoming ones. Copying a group invitation produces
a `/join/<code>` link; recipients sign in and explicitly accept it. Treat invite links as secrets:
any signed-in user with the code can join. Sharing an event URL alone does not grant access.

Extraction is a draft, not a source of truth. Missing titles and dates remain empty for review.
Verify all extracted facts before saving. Screenshots are sent to the configured AI provider;
avoid uploading private information without permission. The application does not persist the
uploaded screenshot. A saved event whose initial sharing fails remains accessible for retry.

Additional authenticated endpoints:

| Method | Path | Purpose |
| --- | --- | --- |
| PUT | `/api/v1/events/{id}` | Owner edits event |
| DELETE | `/api/v1/events/{id}` | Owner deletes event and RSVPs |
| DELETE | `/api/v1/events/{id}/groups/{group_id}` | Owner removes sharing |
| DELETE | `/api/v1/events/{id}/vote` | Withdraw own RSVP |

## Deployment and verification

`/health` is a liveness check; `/ready` verifies database connectivity. Apply migrations before
serving traffic. The API container runs as a non-root user. Use HTTPS, explicit frontend CORS
origins, database backups, and platform-level request/upload limits in production. Add gateway
rate limiting before exposing paid extraction to untrusted traffic. Never put an OpenAI key
or Supabase service-role key in frontend environment variables. Use Supabase asymmetric JWT
signing keys (ES256 or RS256); user tokens must have the `authenticated` role.

GitHub Actions runs backend lint/tests, PostgreSQL migrations/schema checks, and frontend
typechecking, lint, build, and rendering tests. Local verification passed 31 backend tests and
6 frontend tests plus lint, typechecking, and the production build. Backend repository tests
use SQLite; the PostgreSQL migration job must also pass in CI. Live Supabase sign-in, OpenAI
extraction, and hosted browser flows require configured services and are not covered by these
local checks. Docker and a live PostgreSQL instance were not available for local verification.

Release smoke test: sign in with two accounts, create a group, accept its invite, upload and
review a screenshot, save/share the event, RSVP from both accounts, edit as the owner, withdraw
a vote, unshare, and confirm a nonmember cannot read or change the event. Finally delete it
as the owner and confirm it disappears. Verify Supabase email confirmation redirects use your
deployed site URL.
