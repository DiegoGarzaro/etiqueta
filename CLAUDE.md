# Etiqueta — home inventory app

FastAPI + async SQLAlchemy backend (`backend/`, managed with uv), React + Vite
PWA frontend (`frontend/`, Portuguese UI). See `README.md` for the Docker
self-hosting stack and `docs/` for the PRD and design system.

## Access PIN (single-user auth)

The app can be locked with a 4-8 digit PIN (the house QR labels point guests
at the app, so casual access must be gated). How it works:

- Enforced **server-side** by an HTTP middleware in `backend/app/main.py`:
  every `/api/*` and `/media/*` request needs a valid session cookie
  (`inv_session`, HMAC-signed, 90-day TTL). Only `/api/auth/login|status|logout`
  stay public. Root `/health` stays open for the Docker healthcheck.
- The PIN hash and session-signing secret live in the `app_settings` table
  (`backend/app/services/auth.py`). `INV_APP_PIN` seeds the PIN on first boot
  only; afterwards the stored PIN wins and is changed in Ajustes. Changing the
  PIN rotates the secret, signing out all other devices. With no PIN
  configured anywhere, auth is disabled (dev/tests run open).
- Login is rate-limited process-wide: 5 failures → 30 s lockout (429).
- Frontend: `PinGate` (`frontend/src/components/PinGate.tsx`) wraps the router,
  shows the lock screen, and re-locks on any API 401. The URL is preserved, so
  scanning a location QR lands on that location after unlocking.
- Recovery if locked out: delete the `pin_hash` row from `app_settings` (the
  app then starts open again).

## Thermal label printing (Seiko SLP650)

The app prints labels on a Seiko SLP650 attached to a Raspberry Pi that runs a
REST print agent (the `slp650-sdk` project).

### Print server

- Base URL: `http://100.87.166.24:8787` (Tailscale IP of the Pi).
- Auth: `X-API-Key` header. The key lives in the gitignored `.env`
  (`SLP650_API_KEY`; `SLP650_BASE_URL` overrides the default URL) and is read
  by `backend/app/core/config.py`. It must NEVER reach browser code — the
  frontend only calls our backend (`/api/print/*`), which proxies the print
  server (`backend/app/api/routes/printing.py` → `backend/app/services/slp650.py`).
- Key endpoints (details in the SDK docs): `GET /health` (`ok: true` when the
  printer is ready), `GET /templates`, `POST /print/template`
  (e.g. `visitor-badge`: name/company/qr_data), `POST /print/image` (multipart
  PNG/JPEG, fitted to the media), `POST /print/text`. Errors: 401 bad key,
  404 unknown template, 422 bad fields/media, 503 printer offline. All print
  responses include `engine` (`native`/`cups`).

### Printer and media facts

- 300 dpi thermal, 1-bit black/white only. Printhead is 576 dots.
- Loaded roll: SLP-NWB name badges → media name `MediaBadge`, canvas
  **750×567 px** (landscape; x = feed direction). Other media exist
  (`AddressSmall` 984×285, `Shipping` 1131×567, …) but MediaBadge is loaded.
- The feed axis prints ~2% short mechanically; verify printed QR/barcodes with
  a real scanner before relying on them.

### Designing labels in this app

Custom designs are rendered server-side to a 750×567 PNG and sent through
`POST /print/image` (see `backend/app/services/label_image.py`, which renders
the location labels). Rules from the SDK integration guide:

- Pure black on white — no grays, no strokes thinner than 3 px.
- Threshold, don't dither (`convert("1", dither=Image.Dither.NONE)`); reserve
  dithering for photos.
- Auto-fit text instead of fixed font sizes; field values vary in length.
- Fonts: DejaVu Sans (regular + bold) is bundled at
  `backend/app/assets/fonts/` — the Docker image has no system fonts.
- QR modules ≥ 4 px (`_qr_image` handles this).

### SDK docs (read before changing print code)

Local checkout: `~/Documents/dev/slp650-sdk` (github.com/DiegoGarzaro/slp650-sdk,
tag v0.2.0). Most relevant: `docs/11_INTEGRATION_GUIDE.md` (integration +
label-design rules), `docs/07_REST_API.md` (endpoints and errors),
`docs/04_LABEL_MEDIA.md` (media geometry).

### QR origin

Printed QR codes encode `<origin>/locais/<id>`. With `INV_PUBLIC_BASE_URL`
set (deployment: `http://10.0.0.228:8070`, the home server's reserved LAN IP),
that canonical origin is always used — both by the backend label renderer and
by the browser print sheet (via `GET /api/config`). Without it, the printing
browser's own origin is used, which makes labels depend on where they were
printed from. The app is LAN-only over HTTP by design (PIN-gated, never
port-forwarded to the internet); the in-app camera scanner needs HTTPS and is
therefore unavailable — labels are scanned with the phone's native camera.

### App surfaces

- Frontend page: `/impressora` (`frontend/src/pages/PrintPage.tsx`) — printer
  status, location labels with live preview, visitor badges, image upload.
- Backend routes under `/api/print`: `health`, `templates`, `badge`, `image`,
  `locations/{id}` (print) and `locations/{id}/preview.png` (exact preview).
- Tests: `backend/tests/test_printing.py` (mocked transport — no hardware
  needed).
