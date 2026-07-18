# Design System — "Etiqueta"

> The visual identity of a labeled, orderly house. One motif carries the brand: the
> **location code rendered as a physical-looking tag** (`ARM-A · GAV-02`). Everything
> else stays quiet so that tag — and the item photos — do the talking.

## 1. Design principles

1. **The tag is the signature.** A location code is never plain text; it's an *etiqueta*
   — a manila chip with a punch-hole and a monospace code. It ties every digital record
   to the physical label on the furniture.
2. **Photos are content, chrome is paper.** Warm paper surfaces, hairline borders, and
   generous whitespace let item photos and tags stand out.
3. **One accent, used with intent.** Pine green means "action/active". Amber means
   "pay attention". Nothing competes with them.
4. **Mobile hot path first.** The register-an-item flow is designed one-handed, thumb-reachable.
5. **Calm over clever.** This is a tool used standing in front of a drawer — legibility
   and speed beat decoration.

## 2. Typography

| Role | Typeface | Usage |
|---|---|---|
| **Display** | **Bricolage Grotesque** | Screen titles, section headers, empty-state headlines. Weight 600–700. |
| **Body** | **Inter** | All UI text, forms, item names, descriptions. 400/500/600. |
| **Mono (signature)** | **JetBrains Mono** | Location codes, tags, QR captions, IDs, quantities. 500. |

Pairing rationale: Bricolage Grotesque has a slightly humanist, hand-cut quality that
reads warm rather than corporate; Inter keeps dense forms and lists effortlessly legible
in PT-BR (accents included); JetBrains Mono gives codes the unmistakable look of
label-maker tape.

### Type scale (rem, 16px base)

| Token | Size / line-height | Weight | Use |
|---|---|---|---|
| `display-xl` | 2.25 / 1.1 | 700 | Empty-state / landing headline |
| `display-l` | 1.75 / 1.15 | 700 | Screen title |
| `heading` | 1.25 / 1.25 | 600 | Section header |
| `subhead` | 1.0625 / 1.3 | 600 | Card title / item name |
| `body` | 1.0 / 1.5 | 400 | Default text |
| `small` | 0.875 / 1.45 | 400 | Secondary / meta |
| `code` | 0.8125 / 1.2 | 500 | Tags, codes (JetBrains Mono, tracked +0.02em, uppercase) |

## 3. Spacing, radius, elevation

- **Spacing scale (px):** 4 · 8 · 12 · 16 · 24 · 32 · 48. Default gutter 16, section gap 24.
- **Radius:** `--r-sm: 8px` (chips/inputs), `--r-md: 12px` (cards), `--r-lg: 16px` (sheets/modals).
  Tags use `--r-sm` with a punch-hole, not a pill.
- **Elevation:** flat by default; cards use a 1px `--line` border, not shadow. Only overlays
  (modals, the bottom sheet, dropdowns) get shadow: `0 8px 28px rgba(31,36,33,.14)`.

## 4. Signature component — the Etiqueta (location tag)

```
   ┌───────────────────────────┐
 ○ │  ARM-A · GAV-02           │      ○ = punch hole (manila-line)
   └───────────────────────────┘      bg: manila · text: graphite · mono, uppercase
```

- Background `--manila`, 1px `--manila-line` border, `--r-sm`, small left "punch hole".
- Text: JetBrains Mono, `--graphite`, uppercase, tracked.
- Sizes: `sm` (inline in lists), `md` (item detail, tappable → opens location).
- **Full-path variant** separates segments with `›`:
  `Escritório › Armário A › Gaveta 2`, last segment bold.

Use it anywhere a location is referenced: item cards, search results, item detail,
breadcrumbs. It is the one consistently "designed" object in the UI.

## 5. Core components

**Buttons**
- Primary: `--pine` fill, paper text, `--r-sm`; hover `--pine-600`.
- Secondary: paper fill, `--graphite` text, 1px `--line`; hover `--paper-2`.
- Destructive: text/`--rust`; solid `--rust` only in confirm dialogs.
- FAB (mobile): `--pine` circular **+**, bottom-right, primary "Adicionar" action.

**Inputs & forms**
- 44px min height, `--r-sm`, 1px `--line`, focus ring `--pine` 2px offset.
- Location picker: search field + recent + "escanear QR" affordance.
- Category input: autocomplete chips using the category chip palette.

**Item card**
```
┌────────────────────────────────────┐
│ ▢ photo   Carregador USB-C         │
│           [ ARM-A · GAV-02 ]  ×2   │
│           #Eletrônicos             │
└────────────────────────────────────┘
```
Photo thumbnail (`--r-sm`), item name (`subhead`), etiqueta tag, quantity in mono,
category chips.

**Location tree node**
- Type icon + name + descendant item count (mono, `--mist`).
- Chevron to expand; selected node uses `--pine-tint`.

**Category chip**
- Rounded `--r-sm`, colored dot + label; color from category palette.

**Empty states**
- Bricolage headline + one plain-language line + a single action.
  e.g. *"Nada por aqui ainda."* / "Cadastre o primeiro item desta gaveta." / **+ Item**

**QR / scan**
- Full-screen scanner with a framed target, torch toggle, and **"Digitar código"** manual
  fallback. On success, haptic + toast `Local encontrado: ARM-A · GAV-02`.

## 6. Iconography

- Line icons, 1.75px stroke, rounded caps, `--graphite`/`--mist`.
- Location-type glyphs: Cômodo (door), Armário (wardrobe), Gaveta (drawer), Prateleira
  (shelf), Caixa (box), Organizador (grid-bins). Consistent, recognizable set.

## 7. Layout & navigation

- **Mobile:** bottom tab bar — **Buscar · Locais · Categorias · Escanear** — plus the
  primary FAB. Content is single-column, thumb-reachable actions at the bottom.
- **Desktop:** left sidebar (same sections) + wider content; tree and detail side-by-side.
- Screen title uses `display-l`; breadcrumbs use the etiqueta path variant.

## 8. Motion

Restrained and purposeful (respect `prefers-reduced-motion`):
- Sheet/modal: 180ms ease-out slide/fade.
- Tag tap → location: shared-element feel (tag lifts, 150ms).
- Scan success: 120ms scale-pop on the target frame + toast.
- No ambient/decorative animation.

## 9. Voice & copy (PT-BR)

- Active, plain, sentence case. Buttons say what happens: **Salvar**, **Mover**, **Imprimir etiqueta**.
- Consistent verbs across a flow (the button that says **Publicar**… — here: **Salvar** →
  toast **Item salvo**).
- Errors are specific and actionable, in the app's voice, never apologetic:
  *"Escolha um local para o item."* not *"Erro de validação."*
- Empty screens invite action, not mood.
- Domain vocabulary matches the physical world: Local, Armário, Gaveta, Caixa,
  Organizador, Etiqueta, Categoria.

## 10. Accessibility & quality floor

- WCAG AA contrast (see PALETTE.md); visible keyboard focus everywhere.
- Targets ≥ 44px; scanner always has manual entry.
- Reduced-motion honored; dark mode supported; PT-BR accents render correctly.
- Test down to 360px width.

## 11. Design tokens (starter)

```css
:root {
  /* type */
  --font-display: "Bricolage Grotesque", system-ui, sans-serif;
  --font-body: "Inter", system-ui, sans-serif;
  --font-mono: "JetBrains Mono", ui-monospace, monospace;

  /* radius */
  --r-sm: 8px; --r-md: 12px; --r-lg: 16px;

  /* space */
  --s-1: 4px; --s-2: 8px; --s-3: 12px; --s-4: 16px;
  --s-6: 24px; --s-8: 32px; --s-12: 48px;

  /* elevation */
  --shadow-overlay: 0 8px 28px rgba(31,36,33,.14);
}
```

> Colors live in **PALETTE.md**. Import both files' tokens together at app root.
