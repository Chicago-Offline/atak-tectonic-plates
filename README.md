# Tectonic Plates — ATAK vector overlay (KMZ)

Global tectonic plate boundaries, plate outlines and orogens as a single toggleable
KMZ for [ATAK](https://tak.gov). Built from the canonical **PB2002** plate model
(Peter Bird, *An updated digital model of plate boundaries*, Geochemistry Geophysics
Geosystems 4(3), 2003) via the GeoJSON conversion at
[fraxen/tectonicplates](https://github.com/fraxen/tectonicplates) (Hugo Ahlenius).

**Download:** [`tectonic-plates.kmz`](tectonic-plates.kmz) — also published at
<https://chicagooffline.com/downloads/tectonic-plates.kmz>

| | |
|---|---|
| Size | 142,724 B |
| sha256 | `3045c41b721e78a3014f435f7304da663f5e0c7f3a34d47dbf060b324681767a` |
| Placemarks | 312 — 14 `<Polygon>` (orogens only) + 300 `<LineString>`, 2 wrapped in `<MultiGeometry>` |
| Verified | ATAK-CIV 5.8.0.10 (Galaxy Tab Active3 + emulator), clean at globe zoom |

## Install

Push to the device and import:

```sh
adb push tectonic-plates.kmz /sdcard/atak/overlays/
```

ATAK does **not** auto-import a file dropped into `overlays/` while it is running —
use **Overlay Manager → Overlays → scan/refresh**, or restart ATAK. The overlay then
appears under Overlay Manager with one toggleable folder per boundary class.

## Folder structure in Overlay Manager

| Folder | Count | Line colour (`aabbggrr`) |
|---|---|---|
| Subduction zone | 65 | `ff2222cc` red |
| Oceanic convergent | 17 | `ff4466ee` blue |
| Continental convergent | 17 | `ff3399ff` light blue |
| Oceanic spreading ridge | 66 | `ff14ff39` green |
| Continental rift | 23 | `ff44dd88` green |
| Oceanic transform fault | 29 | `ff00e5ff` cyan |
| Continental transform fault | 24 | `ff00b3ff` amber |
| Plate outlines | 57 | `80ffffff` white, `LineString` split at the antimeridian |
| Orogens (diffuse deformation) | 14 | `3000b3ff` amber fill (`<Polygon>`) |

Each line's description carries the plate pair (e.g. *Pacific / North America*)
resolved from `PB2002_plates.json`, plus the original literature `Source` field.

## How boundary class was assigned

`PB2002_boundaries.json` carries a usable `Type` on only **65 of 241** segments
(`subduction`); the other 176 are blank. The class used here is the **dominant
`STEPCLASS`** over each boundary's segments in `PB2002_steps.json` (5,824 steps),
grouped by the `PLATEBOUND` key. Explicit `Type == subduction` wins over the tally.

⚠️ A mixed-character boundary is therefore labelled by its **majority** class, not
per-metre truth. For segment-level fidelity, read `PB2002_steps.json` directly.

## Rendering notes (hard-won — read before adapting)

- All geometry is `<tessellate>1</tessellate>` so lines follow the ellipsoid
  instead of chording through it — required at global scale.
- 🔴 **Every line is split where a segment jumps more than 180° of longitude.**
  ATAK draws a −180°→+180° segment *the long way round the globe*; exactly two
  PB2002 features (North America, Antarctica) contain such a segment, and the two
  runaway sweeps render as large soft white smears over the Pacific.
  `split_dateline()` in the builder cuts them; PB2002 already has vertices on the
  antimeridian, so no geometry is lost. **Any globe-spanning KML destined for ATAK
  should be audited for `|Δlon| > 180` between consecutive vertices.**
- Plate outlines are emitted as `<LineString>` rather than `<Polygon>` — a filled
  ring enclosing a pole triangulates badly. Orogens stay `<Polygon>`: small, local,
  fill correctly.
- Zero `<IconStyle>` elements; nothing renders as a point.
- Coordinates are rounded to 4 dp (~11 m), far below the plate model's own accuracy,
  which halves the KML size. Final `doc.kml` is 447,771 B.

## Rebuilding

```sh
python3 build_tectonic_kml.py
```

Fetches the PB2002 GeoJSON (~10 MB) from `fraxen/tectonicplates` into
`src/tectonic/` on first run, then writes `tectonic-plates.kmz`. The build is
**byte-reproducible** (pinned zip timestamp): a rebuild reproduces sha256
`3045c41b…` exactly.

## Scope

**Reference/educational use.** A global tectonic model is not a navigation or
targeting product. Boundary positions carry tens-of-km uncertainty by nature.

## License & attribution

- **Data:** PB2002, © Peter Bird 2003, via
  [fraxen/tectonicplates](https://github.com/fraxen/tectonicplates), released under
  the [Open Data Commons Attribution License (ODC-By) v1.0](https://opendatacommons.org/licenses/by/1.0/).
  The KMZ is a derived work of that data — attribution preserved here and in the
  KML document metadata.
- **Builder script** (`build_tectonic_kml.py`): MIT, © 2026 Chicago Offline.

Maintained by [Chicago Offline](https://chicagooffline.com).
