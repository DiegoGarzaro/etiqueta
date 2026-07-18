# Inventário Doméstico — "Etiqueta"

A personal, responsive web app to catalog everything in the house and know exactly
where it lives — armários, gavetas, caixas and organizadores, each with its own label.

- **Design direction:** "Etiqueta" — the location code shown as a physical-looking tag
  (`ARM-A · GAV-02`). See [`docs/`](./docs).
- **Stack:** FastAPI + async SQLAlchemy 2.0 (backend) · React + Vite + TypeScript (frontend).

## Structure

```
docs/                 PRD, design system, palette, style tile
backend/              FastAPI + SQLAlchemy API (see backend/README.md)
frontend/             React + Vite PWA (Portuguese UI)
docker-compose.yml    Self-hosting stack (Postgres + backend + nginx)
```

## Self-hosting with Docker (recommended)

A three-service stack — **Postgres**, the **backend**, and **nginx** serving the built
PWA and reverse-proxying `/api` and `/media`. Everything is reached through one port.

| Service   | Image                       | Role                                             | Exposed          |
|-----------|-----------------------------|--------------------------------------------------|------------------|
| `db`      | `postgres:16-alpine`        | Database (volume `db-data`)                       | internal only    |
| `backend` | built from `backend/`       | FastAPI/uvicorn API + photos (volume `media-data`)| internal only    |
| `web`     | built from `frontend/`      | nginx: serves the PWA, proxies `/api` + `/media`  | host `APP_PORT`  |

```bash
cp .env.example .env      # set APP_PORT and a real POSTGRES_PASSWORD
docker compose up -d --build
```

Open `http://your-server:8070` (or whatever `APP_PORT` you chose). Tables are created on
first boot. Data persists in the `db-data` and `media-data` volumes.

```bash
docker compose logs -f          # follow logs
docker compose ps               # service status
docker compose up -d --build    # apply code updates (rebuild changed images)
docker compose down             # stop (keeps data)
docker compose down -v          # stop and DELETE all data + photos
```

### Configuration

Set in `.env` (see `.env.example`):

| Variable            | Default             | Purpose                                          |
|---------------------|---------------------|--------------------------------------------------|
| `APP_PORT`          | `8070`              | Host port the app is published on                |
| `POSTGRES_USER`     | `inventory`         | Database user                                    |
| `POSTGRES_PASSWORD` | `inventory`         | Database password — **change this**              |
| `POSTGRES_DB`       | `inventory`         | Database name                                    |

The backend reads these env vars (compose wires them for you):
`INV_DATABASE_URL` (async DSN, e.g. `postgresql+asyncpg://…`), `INV_MEDIA_DIR`
(`/data/media` in the container), and `INV_CORS_ORIGINS` (empty — same origin via nginx).

> The app is served over plain HTTP. The **camera scanner needs HTTPS** (or localhost),
> so to scan on your phone, put the app behind a reverse proxy with TLS (Caddy, Traefik,
> nginx) or a tunnel. Everything else works over HTTP on your LAN.

### Backups

Use the in-app **Ajustes** page to export JSON/CSV, and copy the `media-data` volume for
photos. Or dump the database directly:

```bash
docker compose exec db pg_dump -U inventory inventory > backup.sql
```

## Run it locally without Docker (two terminals)

**Backend** — http://localhost:8000

```bash
cd backend
uv sync
uv run python -m scripts.seed      # optional sample data
uv run uvicorn app.main:app --reload
```

**Frontend** — http://localhost:5173 (proxies `/api` to the backend)

```bash
cd frontend
npm install
npm run dev
```

## Status

**M1 — walking skeleton (done):** locations tree with auto-generated codes, items with
categories and quantities, categories, accent-insensitive search, item/location **editing
and moving**, and the Etiqueta design system.

**M2 — label system (done):** printable A4 **QR label sheets** (`/etiquetas`) and an
in-app **camera scanner** (`/escanear`) that opens a location on scan. QR codes and
scanning run client-side; the backend is unchanged.

> The scanner needs camera access, which browsers only grant over **HTTPS or localhost**.
> It works in `npm run dev` on localhost; a deployment must be served over HTTPS.

**M3 — photos (done):** attach/capture photos on items and locations (camera on mobile
via the file input). Uploads are stored on disk, EXIF-rotated, and thumbnailed server-side
with Pillow; item cards show the first photo. Images are served from `INV_MEDIA_DIR`
(default `backend/media/`, git-ignored) under `/media`.

**M4 — PWA + backup (done):** installable **PWA** (manifest + service worker via
`vite-plugin-pwa`) with offline reads — API responses cached NetworkFirst, images
CacheFirst. **Ajustes** page exports the whole inventory as **JSON** (re-importable) or
**CSV** (items for spreadsheets), and imports a JSON backup to restore.

> The service worker is built into the production bundle (`npm run build` / `npm run
> preview`); it is disabled in `npm run dev`. Photos live as files in `backend/media/` —
> copy that folder alongside the JSON for a complete backup. Import **replaces** all data.

The PRD roadmap (M1–M4) is complete.

## Quality

```bash
cd backend  && uv run ruff check . && uv run pytest -q
cd frontend && npm run build        # type-checks via tsc
```
