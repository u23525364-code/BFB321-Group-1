---
name: "halfway-dashboard"
description: "Apply the shared Halfway Group colour and formatting theme (palette, type, status and chart colours) to any HPC dashboard page so all pages look uniform."
---

# Halfway Dashboard Theme (formatting only)

This skill defines **only the visual formatting** for HPC dashboards: colours, typography, and how
those are applied. It does **not** decide page content, layout, KPIs, thresholds, data sources, API
calls or navigation; those are specified separately for each page. Never add or assume dashboard
content because of this skill.

The palette follows Halfway Group's live site (heyhalfway.com, Bootstrap theme): black as the
primary, Halfway red as the brand accent, charcoal, light grey surfaces and Montserrat. The
Halfway logo (from heyhalfway.com) lives at `static/img/halfway-logo.png`; use only that file,
in its original red on light surfaces or white (CSS filter) on the charcoal sidebar.

## 0. How this project applies the theme

- **Shell.** Every page is a Jinja template that `{% extends "base.html" %}` and fills
  `title`, `page_title`, `page_subtitle`, `content` and optionally `scripts`. `base.html` provides
  the charcoal sidebar (logo, sectioned icon nav, user/log-out), the white top bar (page title,
  live status, time), Bootstrap, Bootstrap Icons, Montserrat, Chart.js, both stylesheets and
  `static/js/dashboard.js`. Never copy the `<head>`, sidebar or top bar into a page. Pages without
  the shell (login) override `{% block body %}`.
- **Navigation.** Add a page as a route in `app.py` plus an entry in `NAV_SECTIONS`
  (`endpoint`, `label`, Bootstrap Icons class, optional `count`). Links use `url_for(...)`.
- **Files.** `static/css/halfway-theme.css` = tokens and Bootstrap overrides from section 5; do
  not edit unless the palette changes. `static/css/style.css` = shared components below; any new
  class goes there and takes every colour from the variables.
- **Components (reuse before inventing):**
  - Card: `.panel` › `.panel-header` (`.panel-title` + `.panel-subtitle`, actions on the right)
    › `.panel-body` (padded) or `.panel-body-flush` (edge-to-edge tables/lists) › `.panel-footer`.
  - KPI tile: `.kpi-card` › `.kpi-head` (`.kpi-title` + `.kpi-icon`) › `.kpi-value`
    (+ `.kpi-unit`) › `.kpi-meta`. Today's KPIs are the shared `partials/kpi_summary.html`.
  - Table: `.table.table-hw.table-hover`; `.sortable-header` + `onclick="sortTable(i, id)"`;
    `.cell-primary`, `.cell-person` + `.avatar`; numbers `.text-end`.
  - Status pill: `.badge-status` + `.badge-good|warn|crit|none`, sentence-case label.
  - Lists: `.feed-item` (alert rows), `.stat-list` (label/value rows), `.compare-stat`
    (before → after), `.link-card` (home tiles), `.segmented` (tab filter), `.status-strip`.
  - Bars: `.progress` (+ `.progress-xs`) with `.bg-st-*` for status or `.bg-chart-*` for series;
    `.elapsed` for bar + value in a table cell.
  - Charts: Chart.js inside `.chart-box`; colours via `cssVar('--chart-n')`.
  - Page rationale text: `<aside class="design-note">` with a `bi-info-circle` icon.
- **Type.** Headings and labels in sentence case; only `.kpi-title`, `.form-label`, table
  headers and sidebar section labels are uppercase.
- No `<style>` blocks or `style="…"` attributes in templates, except `width`/`height` that
  encode a data value (progress bars).
- Coloured text: `.text-success`, `.text-warning`, `.text-danger` are remapped in `style.css` to
  the *Text* shades, so use those.

## 1. Colour palette

| Token | Hex | Use |
|---|---|---|
| `--hw-red` | `#CF142B` | Brand accent; critical/negative status |
| `--hw-red-dark` | `#A30F22` | Hover on red; red text on red tint |
| `--hw-black` | `#000000` | Primary (hover/active of primary buttons) |
| `--hw-charcoal` | `#2F2F2F` | Navbar/header bars, primary buttons, headings |
| `--hw-ink` | `#222222` | Body text |
| `--hw-muted` | `#555555` | Secondary text, labels, axis text |
| `--hw-navy` | `#162E68` | Links, focus ring, first data series, info |
| `--hw-border` | `#D3D8DC` | Borders, dividers |
| `--hw-surface` | `#F6F6F6` | Page background, table header background |
| `--hw-card` | `#FFFFFF` | Cards, panels |

### Status colours (generic: what each state *means* is decided per page)

| State | Fill (bars, dots, borders) | Text | Tint (pill/row background) |
|---|---|---|---|
| Good | `#00AE49` | `#007A33` | `#E6F6EC` |
| Warning | `#FF8F31` | `#8A4500` | `#FFF1E3` |
| Critical | `#CF142B` | `#A30F22` | `#FBE7E9` |
| Neutral / no data | `#AAAAAA` | `#555555` | `#EEEEEE` |

### Chart series (use in this order)
`#162E68` navy, `#CF142B` red, `#6C7A89` slate, `#FF8F31` amber, `#00AE49` green.
Baseline / comparison / reference series: grey `#AAAAAA`, dashed. Gridlines `#E6E8EA`.

## 2. Colour rules

1. **Red has two jobs only:** brand accent (e.g. a thin rule under the navbar, active-tab underline)
   and critical status. Never use red for decoration, headings or ordinary buttons.
2. **Primary buttons are charcoal**, hovering to black. A red button is allowed for at most one
   hero action per page. Secondary buttons: outline style in charcoal/grey.
3. **Status is never shown by colour alone**: always pair it with a text label and/or icon.
4. **Text contrast ≥ 4.5:1.** Use the *Text* column for coloured text; the *Fill* greens/ambers
   are for shapes only (`#00AE49` on white is only 2.9:1).
5. Use colour sparingly: most of the page is white cards on the light grey surface with charcoal
   text; colour should point at what matters.
6. Never introduce hex codes outside this palette. Reference the CSS variables instead of repeating hex values.

## 3. Typography

- Font: **Montserrat** (Google Fonts, weights 400/500/600/700/800), fallback `system-ui, "Segoe UI", Arial, sans-serif`.
- Body 15px (`.9375rem`), colour `--hw-ink`.
- Page title 24px/700; section/card titles 18px/700; sub-headings 16px/600.
- Small labels (KPI labels, table headers): 12px, 600, uppercase, letter-spacing .05em, `--hw-muted`.
- Big numbers (KPI values): 32px/700, `font-variant-numeric: tabular-nums`.
- Numbers in tables right-aligned with tabular numerals.

## 4. Shape and surfaces

- Card: white, 1px `--hw-border` border, radius 12px (`.75rem`), shadow `0 1px 2px rgba(0,0,0,.06), 0 4px 12px rgba(0,0,0,.04)`.
- Buttons/inputs radius 8px (`.5rem`). Status pills fully rounded.
- Focus ring: 3px solid `--hw-navy`, offset 2px.
- Spacing: Bootstrap spacing utilities only (0.25rem scale); no arbitrary pixel margins.

## 5. Theme file — `static/css/halfway-theme.css`

One shared file, linked after Bootstrap on every page. It holds tokens and Bootstrap overrides only.

```css
:root {
  --hw-red:#CF142B; --hw-red-dark:#A30F22; --hw-red-tint:#FBE7E9;
  --hw-black:#000000; --hw-charcoal:#2F2F2F; --hw-ink:#222222; --hw-muted:#555555;
  --hw-navy:#162E68; --hw-border:#D3D8DC; --hw-surface:#F6F6F6; --hw-card:#FFFFFF;

  --st-good:#00AE49;  --st-good-text:#007A33;  --st-good-tint:#E6F6EC;
  --st-warn:#FF8F31;  --st-warn-text:#8A4500;  --st-warn-tint:#FFF1E3;
  --st-crit:#CF142B;  --st-crit-text:#A30F22;  --st-crit-tint:#FBE7E9;
  --st-none:#AAAAAA;  --st-none-text:#555555;  --st-none-tint:#EEEEEE;

  --chart-1:#162E68; --chart-2:#CF142B; --chart-3:#6C7A89; --chart-4:#FF8F31; --chart-5:#00AE49;
  --chart-baseline:#AAAAAA; --chart-grid:#E6E8EA;

  --hw-radius:.75rem; --hw-radius-sm:.5rem;
  --hw-shadow:0 1px 2px rgba(0,0,0,.06), 0 4px 12px rgba(0,0,0,.04);

  /* Bootstrap 5.3 overrides */
  --bs-body-font-family:"Montserrat", system-ui, -apple-system, "Segoe UI", Arial, sans-serif;
  --bs-body-color:var(--hw-ink);
  --bs-body-bg:var(--hw-surface);
  --bs-border-color:var(--hw-border);
  --bs-link-color-rgb:22,46,104;
  --bs-link-hover-color-rgb:207,20,43;
  --bs-primary-rgb:47,47,47;
  --bs-danger-rgb:207,20,43;
  --bs-success-rgb:0,122,51;
  --bs-warning-rgb:255,143,49;
}
body { font-size:.9375rem; }
:focus-visible { outline:3px solid var(--hw-navy); outline-offset:2px; }
.btn { border-radius:var(--hw-radius-sm); font-weight:600; }
.btn-primary { --bs-btn-bg:var(--hw-charcoal); --bs-btn-border-color:var(--hw-charcoal);
  --bs-btn-hover-bg:var(--hw-black); --bs-btn-hover-border-color:var(--hw-black); --bs-btn-active-bg:var(--hw-black); }
.btn-brand { --bs-btn-color:#fff; --bs-btn-bg:var(--hw-red); --bs-btn-border-color:var(--hw-red);
  --bs-btn-hover-color:#fff; --bs-btn-hover-bg:var(--hw-red-dark); --bs-btn-hover-border-color:var(--hw-red-dark); }
```

Pages may add their own component classes, but those must take every colour, radius and shadow
from these variables.

## 6. Chart.js formatting

Set once globally so every chart matches:

```js
const v = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();
Chart.defaults.font.family = 'Montserrat, system-ui, sans-serif';
Chart.defaults.font.size = 12;
Chart.defaults.color = v('--hw-muted');
Chart.defaults.borderColor = v('--chart-grid');
Chart.defaults.plugins.tooltip.backgroundColor = v('--hw-charcoal');
Chart.defaults.plugins.legend.labels.usePointStyle = true;
// series colours: v('--chart-1') ... v('--chart-5'); baselines: v('--chart-baseline') with borderDash [6,4]
```

In this project these defaults already live in `static/js/dashboard.js` and Chart.js is loaded
by `base.html`; pages only create their charts in `{% block scripts %}`.

## 7. Uniformity check

- [ ] Page extends `base.html`; no hex codes, fonts, `<style>` blocks or non-data inline styles in the page.
- [ ] Only palette colours used; red used only for brand accent or critical status.
- [ ] Status shown with colour + text/icon; coloured text uses the *Text* shades.
- [ ] Montserrat everywhere, including charts.
- [ ] Cards, buttons and radii match section 4.
