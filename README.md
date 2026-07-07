# Shelf Life

> Track your pantry and never let food expire again.

**Shelf Life** helps you keep tabs on the food in your pantry, fridge and
freezer. Add items with quantities and expiration dates, and the app surfaces
what's *expiring soon* or already *expired* so nothing goes to waste.

## Tech Stack

| Layer            | Technology                        |
| ---------------- | --------------------------------- |
| Mobile client    | React Native + TypeScript         |
| Backend API      | Python + FastAPI                  |
| Database         | PostgreSQL (via SQLAlchemy async) |
| Cache            | Redis                             |
| Architecture     | Clean Architecture                |

## Repository Layout

```
.
├── src/                     # FastAPI backend (Clean Architecture)
│   ├── domain/              # Entities, value objects, repository interfaces, domain services
│   ├── application/         # Use cases, DTOs, ports, mappers
│   ├── infrastructure/      # PostgreSQL + Redis adapters, ORM models, config
│   └── interfaces/          # FastAPI app, controllers, schemas, DI composition root
├── tests/                   # Backend unit tests (+ in-memory fakes)
├── mobile/                  # React Native + TypeScript client
├── pyproject.toml           # Backend tooling (ruff, mypy, pytest)
├── requirements*.txt        # Backend dependencies
├── docker-compose.yml       # api + postgres + redis
└── Dockerfile               # Backend image
```

## Database Conventions

Identity is provided by Supabase Auth: every authenticated user has a row in
the Supabase-managed `auth.users` table (not part of our migrations). The
app's own schema builds on top of that id:

- **`public.profiles`** — the public identity for an authenticated user
  (`username`, `display_name`). Its `id` column *is* `auth.users.id` (a
  1:1 FK, `ON DELETE CASCADE`) — a profile has no identity of its own.
  `username` is stored pre-normalized (stripped + lowercased), so a plain
  unique constraint gives case-insensitive uniqueness without a separate
  expression index; a check constraint (`username = lower(username)`)
  defends that invariant against writes that bypass the application layer.
  It also carries a nullable, unique `email` column — a copy of the
  `auth.users` email, kept purely so the forgot-password edge function can
  resolve a username to an email server-side (Supabase Auth's own
  `auth.users` table isn't part of our migrations, so there's no other
  server-side place to look it up from). Nullable because profiles created
  before that column existed have none on file; every new profile supplies
  one.
- **Every user-owned table** (e.g. `inventory_items`, `ratings`,
  `shopping_list_items`, and any future one) carries a
  `user_id uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
  column. New tables should follow this convention rather than inventing a
  separate identity concept.
- **`public.users`** is a taste/dietary-preferences table (allergies, flavor
  profile, taste vector) — despite the name, not an identity table. Its `id`
  is `auth.users.id` (same 1:1-FK pattern as `profiles`), and
  `inventory_items`/`ratings`/`shopping_list_items` FK `user_id` directly to
  `auth.users.id` too, not to this table. Renaming it to something like
  `taste_profiles` to stop it reading as an identity table is a nice-to-have,
  not yet done.

### Row-Level Security

Every table above has RLS enabled, with `SELECT`/`INSERT`/`UPDATE`/`DELETE`
policies scoping rows to the caller: `<id column> = auth.uid()` (`id` for
`profiles`/`users`; `user_id` for the rest). `FORCE ROW LEVEL SECURITY` is
also set, so the policies apply even to the tables' owner.

**Deployment requirement, not optional:** `auth.uid()` returns NULL — and
every policy above denies all rows — for any DB role with the `SUPERUSER` or
`BYPASSRLS` attribute; Postgres never subjects those roles to RLS, `FORCE`
or not. Supabase's default `postgres` connection string is often such a
role. Whatever role `DATABASE_URL` authenticates as **must** be a plain,
non-superuser, non-`BYPASSRLS` role, or RLS is silently a no-op for
everything this backend does.

Because our FastAPI backend talks to Postgres directly rather than through
Supabase's PostgREST gateway (which is what normally populates
`auth.uid()`), it sets the equivalent session claim itself, per request, for
every endpoint that touches a user-owned table — see
`AuthenticatedSessionDep` in `src/interfaces/http/dependencies.py`. Existing
application-layer `user_id` filtering in use cases/repositories is
unchanged and stays in place as a second, independent layer — RLS is a
backstop, not a replacement.

---

## Clean Architecture

This project follows **Clean Architecture**. The layer rules are defined in
`CLAUDE.md`, `architecture.json`, and each layer's own `CLAUDE.md`.

### The layers (backend, in `src/`)

- **`domain/`** — The heart of the app. Pure business rules with **zero**
  outside dependencies.
  - `entities/PantryItem` — a food item that owns its own freshness rules.
  - `value_objects/Quantity` — an immutable amount + unit.
  - `repositories/PantryItemRepository` — an *interface* (what, not how).
  - `services/ExpirationService` — logic spanning many items.

- **`application/`** — Orchestrates the domain to fulfil **use cases**. Imports
  only from `domain/`.
  - `use_cases/` — `AddPantryItem`, `ListPantryItems`, `ConsumePantryItem`,
    each a single class with an `execute(dto)` method.
  - `dtos/` — input/output contracts (never exposes domain entities).
  - `ports/CachePort` — an abstraction the app depends on (implemented by Redis).
  - `mappers/` — domain entity → DTO translation.

- **`infrastructure/`** — Implements the interfaces above. **All I/O lives here.**
  - `repositories/PostgresPantryItemRepository` — fulfils the domain interface.
  - `cache/RedisCache` — fulfils the `CachePort`.
  - `database/` — SQLAlchemy engine + ORM models (ORM types never leak out).
  - `config.py` — the only place environment variables are read.

- **`interfaces/`** — Entry points. Translates HTTP ⇄ use case calls.
  - `http/controllers/` — thin FastAPI routers (validate → call use case → serialize).
  - `http/schemas.py` — Pydantic request/response shapes.
  - `http/dependencies.py` — the **composition root** where concrete
    infrastructure is wired to use cases.

### The Dependency Rule (absolute)

```
interfaces  ──▶  application  ──▶  domain
infrastructure ─▶ application  ──▶  domain
```

- `domain/` imports **nothing** from other layers.
- `application/` imports only from `domain/`.
- `infrastructure/` implements interfaces from `domain`/`application`.
- `interfaces/` calls use cases; it never touches the DB or a domain entity
  directly. The one deliberate exception is the composition root
  (`http/dependencies.py`), which must assemble the dependency graph somewhere.

Because use cases depend only on interfaces, they can be tested against the
`InMemoryPantryItemRepository` in `tests/fakes/` — no database required.

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+ (for the mobile client)
- Docker & Docker Compose (optional, for Postgres + Redis)
- macOS + Xcode + CocoaPods (to run the mobile client on the iOS Simulator —
  `brew install cocoapods` if you don't have it)

### 1. Backend

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements-dev.txt   # or: make install

# Configure environment
cp .env.example .env

# Start PostgreSQL + Redis (via Docker)
docker compose up -d db cache

# Run the API (auto-creates tables in development)
uvicorn src.interfaces.http.app:app --reload   # or: make dev
```

The API is now available at <http://localhost:8000>. Interactive docs:
<http://localhost:8000/docs>.

Run everything (api + postgres + redis) in containers instead:

```bash
docker compose up --build          # or: make up
```

### 2. Backend quality checks

```bash
make test        # pytest
make lint        # ruff check
make format      # ruff format
make typecheck   # mypy (strict)
```

### 3. Mobile client

The mobile client is React Native. Only the iOS native project (`mobile/ios/`)
is set up in this repo today — there's no `mobile/android/` yet.

```bash
cd mobile
npm install

# First run only (and again whenever native deps change):
cd ios && pod install && cd ..

npm run ios      # builds and launches on the iOS Simulator via Xcode's toolchain
```

`npm run ios` starts the Metro bundler automatically if it isn't already
running; run `npm start` yourself first if you want it in its own terminal.

You can also skip the CLI and work directly in Xcode: open
`mobile/ios/ShelfLife.xcworkspace` (**not** the `.xcodeproj`) and hit Run,
picking whichever simulator you want from the scheme dropdown.

Lint / type-check the mobile app:

```bash
npm run lint
npm run typecheck
```

> Point the app at your API by setting `SHELF_LIFE_API_URL`
> (defaults to `http://localhost:8000`). The iOS Simulator shares your Mac's
> network, so the default just works once the backend is running (Step 1).

---

## Example API

```bash
# Add a pantry item
curl -X POST http://localhost:8000/pantry-items \
  -H 'Content-Type: application/json' \
  -d '{"owner_id":"demo-user","name":"Milk","amount":2,"unit":"liter","expiration_date":"2025-01-01"}'

# List a user's items (expiring/expired first)
curl "http://localhost:8000/pantry-items?owner_id=demo-user"

# Consume some of an item (removes it when it hits zero)
curl -X POST http://localhost:8000/pantry-items/<id>/consume \
  -H 'Content-Type: application/json' \
  -d '{"amount":1,"unit":"liter"}'
```

---

## License

MIT
