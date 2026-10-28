---
name: AquaLab Precision System
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#44474d'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#74777e'
  outline-variant: '#c4c6ce'
  surface-tint: '#4a5f7f'
  primary: '#001229'
  on-primary: '#ffffff'
  primary-container: '#0f2744'
  on-primary-container: '#798fb1'
  inverse-primary: '#b2c8ed'
  secondary: '#006591'
  on-secondary: '#ffffff'
  secondary-container: '#39b8fd'
  on-secondary-container: '#004666'
  tertiary: '#001512'
  on-tertiary: '#ffffff'
  tertiary-container: '#002c27'
  on-tertiary-container: '#009f8f'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#d4e3ff'
  primary-fixed-dim: '#b2c8ed'
  on-primary-fixed: '#021c39'
  on-primary-fixed-variant: '#324866'
  secondary-fixed: '#c9e6ff'
  secondary-fixed-dim: '#89ceff'
  on-secondary-fixed: '#001e2f'
  on-secondary-fixed-variant: '#004c6e'
  tertiary-fixed: '#71f8e4'
  tertiary-fixed-dim: '#4fdbc8'
  on-tertiary-fixed: '#00201c'
  on-tertiary-fixed-variant: '#005048'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  display-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '700'
    lineHeight: 40px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Inter
    fontSize: 26px
    fontWeight: '700'
    lineHeight: 34px
    letterSpacing: -0.015em
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.015em
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.01em
  title-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
    letterSpacing: -0.005em
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 16px
  label-md:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.04em
  data-metric:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
    letterSpacing: -0.02em
  data-tabular:
    fontFamily: Inter
    fontSize: 13px
    fontWeight: '500'
    lineHeight: 18px
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 0.75rem
  space-lg: 1.25rem
  space-xl: 2rem
---

## Brand & Style

This design system targets laboratory directors, water quality chemists, environmental compliance officers, and laboratory technicians operating in high-throughput analytical settings. The interface projects clinical authority, absolute data fidelity, and calibrated calm. 

The aesthetic is Modern Laboratory Precision: crisp surface planar divisions, ultra-clean borders, selective luminous cyan indicators, and dense, structured data density. Visual metaphors borrow from optical microscopy, analytical spectra, and calibrated flow instrumentation. The experience eliminates decorative visual friction in favor of operational legibility, strict vertical alignment, high-contrast text rendering, and unambiguous status states that guarantee error-free readings under varied lab lighting environments.

## Colors

The palette establishes an analytical balance between dense, authoritative slate tones and responsive, energetic aquatic hues.

- **Primary Canvas & Surfaces**: Base canvas utilizes `#f8fafc` (Slate 50), stepping up to `#ffffff` for elevated analytical cards, tables, and inspection panels. Recessed backgrounds (toolbars, metadata trays) leverage `#f1f5f9` (Slate 100).
- **Structural Lines**: Borders and divisional lines rely exclusively on `#e2e8f0` (Slate 200) to construct razor-sharp grids without optical weight.
- **Brand Navy Anchor**: `#0f2744` serves as primary text, strong framing, deep sidebar backgrounds, and dominant headers, with `#1e3a5f` handling secondary interactive states and table headers.
- **Scientific Accents**:
  - Cyan (`#0ea5e9`): Primary interactive action items, active navigational indicators, calibration focal points.
  - Teal/Turquoise (`#14b8a6`): Verified compliance markers, purity indices, completed batch validations.
  - Sky Tint (`#e0f2fe`): Low-saturation background wash for active selections and badges.
- **Semantic Operational States**:
  - **Nominal / Safe**: Emerald (`#10b981`), light tint (`#ecfdf5`), border (`#a7f3d0`).
  - **Attention / Recalibrate**: Amber (`#f59e0b`), light tint (`#fffbeb`), border (`#fde68a`).
  - **Contaminant / Critical**: Rose (`#f43f5e`), light tint (`#fff1f2`), border (`#fecdd3`).

## Typography

Typography prioritizes micro-legibility and precision across dense multi-column arrays.

- **System Font Family**: Inter is applied across all roles. For numbers, quantitative readouts, PPM metrics, ion chromatography values, and sample timestamps, enforce OpenType tabular figures (`font-feature-settings: "tnum" 1, "cv05" 1, "cv11" 1`) to ensure perfect vertical decimal column alignment.
- **Hierarchy Rules**: 
  - `label-sm` is reserved for technical tags, metric units (e.g., `mg/L`, `μS/cm`, `NTU`), table column headers, and lifecycle state flags, styled with uppercase transformation.
  - Page titles employ `headline-lg` or `display-lg` rendered in deep slate `#0f2744`.
  - Body text uses `#334155` for balanced contrast that reduces eye fatigue over prolonged data entry sessions.

## Layout & Spacing

The layout model is a structured hybrid grid designed for rigorous laboratory data displays.

- **Application Shell**: A fixed 260px vertical navigation sidebar on the left, an auxiliary contextual workbench/filter tray (collapsible 320px) on the right when analyzing specimens, and a flexible main workspace in the center.
- **Grid Architecture**: 
  - Desktop (≥1280px): 12-column fluid grid, 24px (`1.5rem`) gutters, 32px (`2rem`) outer canvas margins.
  - Tablet (768px - 1279px): 8-column grid, 16px (`1rem`) gutters, 24px margins. Navigation shifts to a compact icon-rail (64px).
  - Mobile (<768px): 4-column grid, 12px gutters, 16px margins. Primary tables transform into stacked analytical cards; secondary panels dock into bottom sheets.
- **Component Rhythm**: Inner metric cards and sample logs prioritize vertical compactness: 12px (`0.75rem`) internal padding for dense tables, expanding to 20px (`1.25rem`) for high-level summary cards.

## Elevation & Depth

Depth is established through planar stratification and precise low-contrast outlines rather than heavy cast shadows, reinforcing an aseptic, lab-grade digital environment.

- **Level 0 (Canvas Base)**: `#f8fafc`. Flat, non-interactive foundation.
- **Level 1 (Surface Cards & Grids)**: `#ffffff` background with a crisp 1px solid border in `#e2e8f0`. Shadow is absent or minimal: `0 1px 2px 0 rgba(15, 39, 68, 0.04)`.
- **Level 2 (Hovered Records & Floating Controls)**: `#ffffff` background with 1px solid `#cbd5e1`, accompanied by an ambient clinical shadow: `0 4px 12px -2px rgba(15, 39, 68, 0.06), 0 2px 4px -1px rgba(15, 39, 68, 0.03)`.
- **Level 3 (Modals, Slide-over Run Detail Drawers)**: 1px border `#cbd5e1`, supported by `0 16px 32px -6px rgba(15, 39, 68, 0.12), 0 4px 8px -2px rgba(15, 39, 68, 0.04)`.
- **Subsurface Recession**: Filter docks, disabled states, and nested formula bars use `#f1f5f9` paired with an inset line (`border: 1px solid #e2e8f0`).

## Shapes

The design system employs a disciplined, soft geometry (`roundedness: 1`). 

- **Containers & Data Surfaces**: Form elements, tables, status panels, and data cards utilize `0.25rem` (4px) or `0.375rem` (6px) corner radiuses. This tight radius conveys mechanical calibration and structural precision.
- **Status Pills & Chips**: Retain a subtle distinction; chips use `0.25rem` (4px) corner radii for structural harmony with surrounding tabular cells, rather than full rounded capsules.
- **Focus Rings**: Sharp 2px offset rings (`outline-offset: 2px`) rendered in `#0ea5e9` with zero corner distortion, mirroring optical lenses.

## Components

### Buttons
- **Primary**: Background `#0f2744`, text `#ffffff`, border 1px solid transparent. Hover: `#1e3a5f`. Active: `#0a1c32`. Focus: 2px ring `#0ea5e9`.
- **Secondary / Action**: Background `#0ea5e9`, text `#ffffff`. Hover: `#0284c7`.
- **Outline / Lab Tool**: Background `#ffffff`, text `#1e3a5f`, border 1px solid `#cbd5e1`. Hover: Background `#f8fafc`, border `#94a3b8`.
- **Metrics / Compact**: Height 32px, padding 0 12px, font size 13px, weight 500.

### Badges & Analytical Chips
- Compact height (22px), `0.25rem` radius, 6px horizontal padding.
- **Compliant / Pure**: Background `#ecfdf5`, border 1px solid `#a7f3d0`, text `#065f46`, uppercase font weight 600 (`label-sm`).
- **Monitoring / In Review**: Background `#e0f2fe`, border 1px solid `#bae6fd`, text `#0369a1`.
- **Deviation / Critical**: Background `#fff1f2`, border 1px solid `#fecdd3`, text `#9f1239`.

### Data Tables
- Headers: Background `#f8fafc`, text `#475569`, border-bottom 1px solid `#cbd5e1`, uppercase 11px font weight 600.
- Rows: Background `#ffffff`, height 40px (compact) or 48px (standard), border-bottom 1px solid `#e2e8f0`. Hover row: `#f1f5f9`.
- Tabular figures applied to all numeric cells; right-aligned with unit descriptors in `#64748b`.

### Form Inputs & Selects
- Background `#ffffff`, border 1px solid `#cbd5e1`, height 36px, padding 0 10px, text `#0f2744`.
- Focus: Border `#0ea5e9`, ring 2px translucent cyan (`rgba(14, 165, 233, 0.15)`).
- Prefix / Suffix units: Hard-docked span background `#f1f5f9`, border-right 1px solid `#cbd5e1`, text `#64748b`.

### Checkboxes & Radios
- Size 16px × 16px, border 1.5px solid `#94a3b8`, background `#ffffff`, radius 3px (checkbox) or circle (radio).
- Checked: Background `#0ea5e9`, border `#0ea5e9`, check icon crisp white.

### Laboratory Specific Components
- **Spectrogram & Assay Cards**: White container, 1px `#e2e8f0` border, featuring a top 3px accent line colored dynamically according to sample status (Cyan: In Process, Teal: Certified, Rose: Out of Spec).
- **Sample Chain-of-Custody Stepper**: Horizontal track 2px solid `#e2e8f0`, active nodes highlighted in `#0ea5e9` with pulse ring, completed nodes in `#14b8a6`.
- **PPM Tolerance Bar**: Micro progress track (4px height) with nominal zone demarcations, high/low limit stops, and a needle indicator showing analyte levels.