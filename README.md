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
