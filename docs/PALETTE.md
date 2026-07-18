# Palette — "Etiqueta"

> Rooted in the materials of an organized house: warm paper, kraft/manila tags,
> label-maker ink, and the calm green of storage bins. Deliberately **not** the
> default cream + terracotta — the primary accent is **pine green**, and amber is
> reserved strictly for attention states.

## Core palette

| Token | Name (PT) | Hex | Role |
|---|---|---|---|
| `--paper` | Papel | `#FBF9F4` | App background / surfaces |
| `--paper-2` | Papel Fundo | `#F2EEE4` | Sunken areas, list stripes |
| `--graphite` | Grafite | `#1F2421` | Primary text, ink (near-black, green undertone) |
| `--graphite-70` | Grafite Suave | `#3B423D` | Secondary text |
| `--pine` | Pinho | `#2F6B4F` | **Primary** — actions, active nav, links, brand |
| `--pine-600` | Pinho Escuro | `#245840` | Hover/pressed on primary |
| `--pine-tint` | Pinho Névoa | `#E4EEE7` | Primary-tinted backgrounds, selected rows |
| `--manila` | Manila | `#E4C9A0` | Tag/label chips (the "etiqueta") |
| `--manila-line`| Manila Traço | `#C9A96B` | Tag borders, punch-hole detail |
| `--mist` | Névoa | `#8A938C` | Muted text, borders, disabled |
| `--line` | Traço | `#E1DCD0` | Hairlines, dividers, card borders |

## Semantic / status

| Token | Name (PT) | Hex | Use |
|---|---|---|---|
| `--amber` | Âmbar | `#E08A3C` | Attention / "needs review" / low quantity |
| `--amber-tint`| Âmbar Névoa | `#F8E9D6` | Amber background |
| `--rust` | Ferrugem | `#B23A2E` | Destructive / delete / errors |
| `--rust-tint` | Ferrugem Névoa | `#F6DED9` | Error background |
| `--sky` | Sereno | `#3E7CA6` | Informational (scan hints, tips) |

## Category chip palette

Distinct, equal-weight hues for user categories — legible on `--paper`, harmonized
with the core palette (muted, not neon):

| Hex | Suggested category |
|---|---|
| `#2F6B4F` | Eletrônicos |
| `#3E7CA6` | Documentos |
| `#B27B2E` | Ferramentas |
| `#7A5AA0` | Papelaria |
| `#A6484B` | Cozinha |
| `#4E7A4A` | Limpeza |
| `#8A6D3B` | Roupas / Têxtil |
| `#5B6670` | Diversos |

## Dark mode

| Token | Hex |
|---|---|
| `--paper` | `#141715` |
| `--paper-2` | `#1C201D` |
| `--graphite` (text) | `#ECE9E1` |
| `--graphite-70` | `#B7BCB4` |
| `--pine` | `#5FAE86` |
| `--pine-tint` | `#1E2A24` |
| `--manila` | `#B79A66` |
| `--line` | `#2A2F2B` |
| `--amber` | `#E7A24E` |
| `--rust` | `#D46A5E` |

## Contrast checks (WCAG)

- `--graphite` on `--paper`: ~14.5:1 (AAA).
- `--pine` on `--paper`: ~4.9:1 (AA for text, AAA large).
- White on `--pine`: ~4.7:1 (AA) — use `--pine-600` for small text on colored buttons.
- `--graphite` on `--manila`: ~9:1 (AAA) — tags are always dark ink on manila.
- `--amber`/`--rust` used with dark text on their `-tint` backgrounds, never as body text.

## CSS variables

```css
:root {
  --paper: #FBF9F4;      --paper-2: #F2EEE4;
  --graphite: #1F2421;   --graphite-70: #3B423D;
  --pine: #2F6B4F;       --pine-600: #245840;  --pine-tint: #E4EEE7;
  --manila: #E4C9A0;     --manila-line: #C9A96B;
  --mist: #8A938C;       --line: #E1DCD0;
  --amber: #E08A3C;      --amber-tint: #F8E9D6;
  --rust: #B23A2E;       --rust-tint: #F6DED9;
  --sky: #3E7CA6;
}
:root[data-theme="dark"] {
  --paper: #141715;      --paper-2: #1C201D;
  --graphite: #ECE9E1;   --graphite-70: #B7BCB4;
  --pine: #5FAE86;       --pine-600: #4E997333; --pine-tint: #1E2A24;
  --manila: #B79A66;     --manila-line: #8A6D3B;
  --mist: #7C857D;       --line: #2A2F2B;
  --amber: #E7A24E;      --amber-tint: #2E2418;
  --rust: #D46A5E;       --rust-tint: #2E1C19;
  --sky: #6BA6CE;
}
```
