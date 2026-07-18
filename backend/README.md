# Backend — Inventário Doméstico

Async FastAPI + SQLAlchemy 2.0 API for the "Etiqueta" home inventory app.
Layered as **routes → services → repositories → models**, async throughout.

## Requirements

- Python ≥ 3.12
- [uv](https://docs.astral.sh/uv/)

## Setup

```bash
cd backend
uv sync
cp .env.example .env   # optional; SQLite defaults work out of the box
```

## Run

```bash
uv run uvicorn app.main:app --reload
```

- API docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

Optionally load sample data:

```bash
uv run python -m scripts.seed
```

## Test & lint

```bash
uv run pytest -q
uv run ruff check .
```

## Layout

```
app/
  core/          config + async engine/session
  models/        SQLAlchemy models (location, item, category)
  schemas/       Pydantic request/response models
  repositories/  data access (one per aggregate)
  services/      business logic (code generation, tree, search)
  api/routes/    thin HTTP handlers
tests/           end-to-end API tests
scripts/seed.py  sample data
```

## Notes

- **Database:** defaults to zero-config SQLite (`inventory.db`). Swap `INV_DATABASE_URL`
  for Postgres (`postgresql+asyncpg://…`) in production.
- **Tables:** created automatically on startup for the walking skeleton. Introduce
  Alembic migrations before the first real deployment.
- **Location codes:** armários are lettered (`ARM-A`), other types numbered (`GAV-02`);
  the tag `full_code` joins non-room ancestors (`ARM-A · GAV-02`). QR deep links use the
  location id, not the code.
```
