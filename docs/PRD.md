# PRD — Inventário Doméstico ("self_inventory")

> Product Requirements Document · v1.0 · 2026-07-13
> Owner: Diego Garzaro · Personal project

---

## 1. Overview

A personal, responsive web app to catalog everything in the house and know
**exactly where each item lives**. As the house gets organized into *armários*,
*gavetas*, *caixas* and *organizadores* — all physically labeled — the app is the
digital twin of that physical system: scan a QR label on a drawer and see what's
inside; search "carregador USB-C" and learn it's in `ARM-A · GAV-02`.

- **Platform:** Responsive web app (mobile-first, works on phone and desktop).
- **Language:** Portuguese (BR) UI.
- **Location model:** QR-code labels + photos of locations and items.
- **Users:** Single household (Diego), optionally shared with family members later.

## 2. Problem & Goals

**Problem.** Physically labeling storage is only half the solution — you still can't
remember which of 40 labeled boxes holds the spare HDMI cable, and you can't search a
label with your eyes. Re-finding and re-buying items you already own wastes time and money.

**Goals.**

1. Register any item in under 20 seconds from a phone (photo + name + location).
2. Answer "onde está X?" instantly via search.
3. Answer "o que tem aqui?" instantly by scanning a location's QR code.
4. Browse the whole house by **location tree** or by **category**.
5. Never lose the mapping between a physical label and its digital record.

**Non-goals (v1).**

- Multi-household / marketplace / sharing with strangers.
- Barcode-based product lookups from external catalogs.
- Inventory valuation, insurance exports, purchase-order workflows.
- Native iOS/Android apps (PWA install is enough).

## 3. Core Concepts (domain model)

| Concept | PT-BR | Description |
|---|---|---|
| **Location** | Local | A place that holds items or other locations. Has a QR code. |
| **Location type** | Tipo de local | `Cômodo`, `Armário`, `Gaveta`, `Prateleira`, `Caixa`, `Organizador`. |
| **Item** | Item | A physical thing stored in exactly one location. |
| **Category** | Categoria | Cross-cutting tag for items (`Eletrônicos`, `Ferramentas`, `Documentos`…). |
| **Photo** | Foto | Image attached to an item or a location. |
| **Code** | Código | Human + QR identifier of a location, e.g. `ARM-A · GAV-02`. |

**Locations are a tree.** A `Cômodo` contains `Armários`; an `Armário` contains
`Gavetas`/`Prateleiras`; those contain `Caixas`/`Organizadores`; any level can hold items.
An item's **full path** (`Escritório › Armário A › Gaveta 2`) is what the user reads.

**Categories are flat tags**, independent of location. An item has one location and
zero-or-more categories.

## 4. Location Codes & QR

- Every location gets a short, human-readable **code** built from its path segments:
  `ARM-A`, `ARM-A/GAV-02`. Codes are stable and printable on a physical label.
- The app generates a **printable QR label sheet** (A4, multiple per page) encoding a
  deep link `.../l/{location_id}`.
- Scanning a QR (in-app scanner or phone camera) opens that location's contents directly.
- The physical label shows: the QR, the human code (`ARM-A · GAV-02`), and the location name.

## 5. Personas & Primary Journeys

**Persona:** Diego, organizing the whole house over several weekends, phone in hand,
standing in front of an open drawer.

**J1 — Register an item (the hot path).**
Open app → tap **+ Item** → snap photo → type name → confirm/adjust the pre-filled
location (from last-scanned QR or search) → optionally add category → **Salvar**.
Target: < 20s, one-handed.

**J2 — Find an item.**
Search bar → type name → results show item, thumbnail, and **full location path** as a
tappable tag → tap to see the location and its neighbors.

**J3 — Audit a location.**
Scan drawer QR (or open in tree) → see every item inside with photos → mark items
moved/removed → done.

**J4 — Set up a new storage unit.**
**+ Local** → choose type + parent → name it → app assigns code → **print QR label** →
stick it on the furniture.

## 6. Functional Requirements

### 6.1 Items
- Create/edit/delete item: name (required), description, quantity (default 1),
  location (required), categories (0..n), photos (0..n).
- Photo capture from camera or upload; first photo is the thumbnail.
- Move item to another location (single action, keeps history optional/v2).
- Item detail shows: photos, full location path (tag), categories, quantity, notes.

### 6.2 Locations
- Create/edit/delete location: name (required), type (required), parent (optional →
  root = cômodo), photo, notes.
- Auto-generated stable code; regenerate only on explicit request.
- Tree browser: expand/collapse; show item counts per node (including descendants).
- Location detail: photo, code + QR, direct items, child locations.
- Print QR labels (single or batch selection → A4 PDF).
- Prevent deleting a non-empty location without confirmation (offer "move contents").

### 6.3 Categories
- CRUD categories with name + color + optional icon.
- Browse all items in a category, across locations.
- Suggest existing categories while typing (autocomplete).

### 6.4 Search & Browse
- Global search over item name, description, category, and location code/name.
- Fuzzy/accent-insensitive matching (`camera` finds `câmera`).
- Filters: by category, by location subtree, has-photo.
- Two primary browse modes: **Por Local** (tree) and **Por Categoria** (grid).

### 6.5 QR / Scanning
- In-app camera scanner (web `getUserMedia` + QR decode).
- Scanning a location QR → location detail. Scanning while in "add item" → pre-fills location.

### 6.6 Photos
- Client-side resize/compress before upload.
- Store originals + thumbnails; lazy-load in lists.

### 6.7 Offline / PWA (v1.5, nice-to-have)
- Installable PWA; read cached data offline; queue writes for sync.

## 7. Non-Functional Requirements

- **Performance:** search results < 300ms on a few thousand items; image lists virtualized.
- **Mobile-first:** every hot path completable one-handed on a phone.
- **Accessibility:** WCAG AA contrast, visible keyboard focus, reduced-motion respected,
  scanner has a manual-entry fallback.
- **Data safety:** export full inventory to JSON/CSV; nightly backup of DB + images.
- **Privacy:** single-tenant, auth-gated; photos are private to the household.

## 8. Suggested Tech (aligns with existing preferences)

> Backend rules already in place: async SQLAlchemy, async-first, SOLID, Google-style
> docstrings, `uv`, `ruff`.

- **Backend:** Python + FastAPI (async), **async SQLAlchemy 2.0**, Alembic, PostgreSQL.
  Managed with `uv`; linted with `ruff`.
- **Storage:** object storage or local volume for images (S3-compatible or filesystem).
- **Frontend:** React + Vite (TypeScript), PWA, a QR decode lib, camera capture.
- **QR:** server-side PDF label generation (e.g. `qrcode` + `reportlab`/`weasyprint`).
- **Auth:** simple single-user session / passkey; expandable to household members.

## 9. Data Model (first cut)

```
location
  id, name, type, parent_id (nullable), code, photo_id (nullable),
  notes, created_at, updated_at
item
  id, name, description, quantity, location_id, notes,
  created_at, updated_at
category
  id, name, color, icon
item_category            (m:n)  item_id, category_id
photo
  id, url, thumb_url, width, height, owner_type(item|location), owner_id
```

Indexes: `item.location_id`, `item.name` (trigram/unaccent), `location.parent_id`,
`location.code (unique)`.

## 10. Milestones

- **M1 — Core CRUD:** locations tree, items, categories, search. (Walking skeleton)
- **M2 — The label system:** codes, QR generation, printable label sheets, scanner.
- **M3 — Photos & polish:** capture/compress, thumbnails, category grid, filters.
- **M4 — PWA & backup:** installable, offline reads, export/import, backups.

## 11. Success Criteria

- I can register a real drawer's worth of items in one sitting without friction.
- For any item I own, I can find its location in < 10 seconds.
- Scanning any labeled unit shows its true contents.
- Six months later, the digital and physical states still match.

## 12. Open Questions

- Household sharing in v1 or later? (assumed later)
- Quantity/consumables tracking depth (do we decrement on use)? (assumed: simple count)
- History/audit log of moves? (assumed v2)
