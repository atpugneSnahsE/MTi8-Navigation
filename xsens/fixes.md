# MTi-8 Navigation Dashboard — Redesign Specification

## 1. Purpose

The current dashboard exposes every value the sensor produces, which is correct — nothing here is optional telemetry, all of it matters for diagnosing GNSS/INS health in the field. The problem is not *what* is shown, it's *how*. Every field currently has equal visual weight, the two hero charts (trajectory + map) don't communicate with each other, and the three bottom strip‑charts are too small to read. This document proposes a layout that keeps 100% of the existing data points but organizes them by function, adds status‑driven color coding, and fixes the wasted/underused chart space.

---

## 2. Audit of the current design

| Issue | Impact |
|---|---|
| 38+ label/value pairs in one flat two‑column list | No scan path; critical values (Fix, PPS, Filter) look identical to low‑priority ones (Temp, Clock) |
| RTK Trajectory plot is empty/unscaled (fixed 0–1 axes) | ~35% of screen width shows a blank grid |
| Roll/Pitch/Yaw strip charts are ~280×150px with auto‑scaled Y axes | A 0.002° noise band renders as a full-height cliff — visually alarming but numerically meaningless |
| Map and trajectory plot are disconnected | Two separate representations of the same position data, neither shows heading/course-made-good together |
| Only 2 fields (Nav Qual, NTRIP) get color coding | Other equally critical flags (PPS: NO, Carrier: ---, Filter: ---) don't visually stand out as degraded/missing |
| No grouping by subsystem | Position, velocity, attitude, DOP/quality, and RTCM/NTRIP fields are interleaved rather than clustered |
| Fixed pixel layout | Doesn't reflow for smaller viewports |

---

## 3. Information architecture

Group the 38 fields into 6 functional clusters instead of 1 flat list. All fields are retained — this is a re-grouping, not a reduction.

1. **Header / Link Status** — Packet, UTC, Connected state (persistent top bar)
2. **Fix & Quality** — Status, Fix, Sat, Differential, Carrier, Filter, GNSS, Nav Qual, HDOP, PDOP, VDOP, Hdg Acc
3. **Position** — Latitude, Longitude, Altitude, MSL
4. **Velocity & Motion** — Vel N, Vel E, Vel D, Speed, H Motion, H Vehicle, H/V/S Accuracy
5. **Attitude** — Roll, Pitch, Yaw (numeric readout + sparkline, inline — replaces the 3 oversized standalone charts)
6. **Correction Link (RTCM/NTRIP)** — NTRIP, Carrier, Clock, PPS, RTCM Pkts/Rate/Age/Writes, Temp

---

## 4. Layout wireframe

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ● Connected   MTi-8 Navigation Dashboard          Packet 36661  UTC ...  │ ← persistent header, status dot
├───────────────┬───────────────┬───────────────┬─────────────────────────┤
│ FIX & QUALITY │   POSITION    │  VELOCITY &    │                         │
│ (status card) │ (status card) │   MOTION       │        MAP              │
│               │               │ (status card)  │   (trajectory drawn     │
├───────────────┴───────────────┴────────────────│    ON the map as a      │
│           ATTITUDE (Roll/Pitch/Yaw)             │    colored polyline,    │
│   compass/attitude widget + 3 inline sparklines │    replaces the blank   │
├──────────────────────────────────────────────────  standalone RTK plot)  │
│         CORRECTION LINK (RTCM / NTRIP)          │                         │
│   status chips + packet-rate sparkline          │                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key change:** the empty "RTK Trajectory" scatter plot is merged into the map panel as a live polyline overlay on the actual OSM basemap (position already known — no reason to duplicate it on a separate blank Cartesian plot). This reclaims ~30% of screen real estate for the grouped status cards.

---

## 5. Component specs

### 5.1 Header bar (persistent, always visible)
- Left: connection status dot (green solid = connected, amber pulsing = degraded, red = lost) + app title
- Right: Packet counter, UTC timestamp
- Height: 48px, no change needed structurally — already efficient

### 5.2 Status cards (Fix & Quality / Position / Velocity / Correction Link)
- Each cluster becomes a **card** with a title, not a bare label list
- Field rows use a consistent `label — value — unit` alignment (right-aligned numerics for scannability)
- **Color-coded value chips**, not just text, driven by thresholds:
  - Fix: `3D` + Differential=YES → green chip
  - PPS: `NO` → amber chip (was invisible before)
  - Carrier / Clock / Filter: `---` → gray "N/A" chip, visually distinct from an actual bad reading
  - HDOP/PDOP/VDOP: green <1.0, amber 1.0–2.5, red >2.5
  - H/V/S Accuracy: green <1.0m, amber 1.0–3.0m, red >3.0m
- Cards collapse to accordions on narrow viewports (see §7)

### 5.3 Attitude panel
- Replace the three separate 280×150 strip charts with:
  - One compact **attitude indicator widget** (artificial-horizon-style icon) driven by Roll/Pitch, plus a compass rose driven by Yaw — gives an at-a-glance sanity check no number list can
  - Numeric Roll/Pitch/Yaw values printed large next to the widget
  - Small inline sparklines (last 60s) under each number, **fixed, physically meaningful Y-axis ranges** (e.g. ±5° or ±30°, not auto-fit to noise) so a flat line reads as "stable," not as a cliff
- This uses less vertical space than the current 3 standalone charts while conveying more (it currently takes ~150px height across 3 separate boxes; the compass+numbers can fit in ~140px total)

### 5.4 Map + Trajectory (merged)
- Base: existing Leaflet/OSM map, unchanged
- Add: trajectory polyline drawn directly on the map in the vehicle's actual GPS track (colored by speed or by Nav Qual if desired)
- Add: heading arrow on the marker driven by Yaw, so attitude and position are visually fused
- Remove: the separate blank "RTK Trajectory" Cartesian (East/North) plot — its data is 1:1 redundant with the map once the polyline is drawn there. If a local-frame ENU plot is genuinely needed for engineering (not just display), move it to a secondary tab, not the main view.

### 5.5 Correction Link panel
- NTRIP / PPS / Carrier / Clock / Filter shown as **status chips** in a single row (not stacked label rows) — these are binary/tri-state flags, so a chip row reads faster than a label list
- RTCM Pkts / Rate / Age / Writes shown as a compact table with a tiny sparkline for RTCM Rate (packets/sec over last 60s) so a drop in correction stream is visible before RTCM Age climbs
- Temp shown here too (it's currently orphaned mid-list with no clear home); when unavailable (`---`) it's de-emphasized rather than taking a full-weight row

---

## 6. Color & typography system

| Token | Use | Color |
|---|---|---|
| `status-good` | Fix 3D+Diff, Nav Qual GOOD, DOP<1.0 | `#22c55e` |
| `status-warn` | PPS NO, DOP 1.0–2.5, accuracy borderline | `#f59e0b` |
| `status-bad` | Fix lost, RTCM Age stale, DOP>2.5 | `#ef4444` |
| `status-na` | `---` fields (Carrier, Clock, Filter, Temp when unset) | `#9ca3af` (muted, not alarming) |

- Labels: 12px medium, muted gray — de-emphasized relative to values
- Values: 16–18px semibold, high contrast — this is the scan target
- Card titles: 13px uppercase, letter-spaced, low-emphasis (structure, not content)
- Numeric alignment: right-align all values within a card for fast vertical comparison

---

## 7. Responsive behavior

- **Desktop (>1400px):** 4-card grid on top row + attitude/correction row below + map on the right, as wireframed in §4
- **Tablet (900–1400px):** cards stack 2-per-row, map moves below the cards, still full width
- **Narrow (<900px):** each card becomes a collapsible accordion (Fix & Quality expanded by default since it's the primary health check), map and attitude widget remain visible above the accordions

---

## 8. What is explicitly preserved

Per requirement, **no field is removed**. Every value currently on screen (Packet, UTC, Status, Fix, Sat, Differential, Carrier, Clock, PPS, Filter, GNSS, HDOP, PDOP, VDOP, Temp, Lat, Lon, Altitude, MSL, Vel N/E/D, Speed, H Motion, H Vehicle, H/V/S Accuracy, Hdg Acc, Nav Qual, Roll, Pitch, Yaw, NTRIP, RTCM Pkts/Rate/Age/Writes) has a defined home in the new layout — the change is purely organizational: grouping by subsystem, color-coding by threshold, replacing the blank duplicate trajectory plot with a merged map overlay, and replacing three oversized noisy strip charts with a compact attitude widget plus fixed-scale sparklines.

---

## 9. Suggested implementation notes

- Grid layout: CSS Grid with named template areas (`header`, `fix`, `position`, `velocity`, `attitude`, `correction`, `map`) — makes the responsive reflow in §7 a matter of redefining `grid-template-areas` per breakpoint, no component rewrites
- Sparklines: fixed-domain (not auto-scaled) small multiples, ~60px tall, sharing a common 60-second rolling window across Roll/Pitch/Yaw/RTCM-rate for visual consistency
- Threshold config should live in one lookup table (field → thresholds → color token) so status-card and chip coloring stay consistent and easy to retune per sensor spec