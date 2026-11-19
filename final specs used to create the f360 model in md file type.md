# Snow Thrower Ignition Push Key — Master Design Specification (V5 Gold Standard)

## 1. Design Overview & Coordinate Datum
- **Part Name:** `HandleBody [KEY]` (Unified single B-Rep solid created by joining `STEM`, `GUARD`, and `HANDLE` subcomponents)
- **Overall Envelope:** `60.50 mm` (X) × `27.00 mm` (Y) × `17.00 mm` (Z)
- **Origin & Datum (`0, 0, 0`):** Centered on the front stem-side face of the Guard collar (`X = 0.00 mm`), symmetric across both the **XY mid-plane (`Z = 0`)** and **XZ mid-plane (`Y = 0`)**.
  - `+X`: Stem insertion axis (`X = 0.00` to `+33.50 mm`)
  - `-X`: Guard collar (`X = 0.00` to `-3.00 mm`) and Handle grip (`X = -3.00` to `-27.00 mm`)
  - `±Y`: Transverse width axis
  - `±Z`: Vertical thickness axis

---

## 2. Modeling Architecture & CAD Rules (Fusion 360 Parametric)
1. **Parametric Mode Only:** All 29 dimensions must be defined as named User Parameters prior to sketching, with sketch dimensions driven by parameter expressions.
2. **100% Fully Constrained Sketches:** Every sketch must achieve full constraint lock (`isFullyConstrained == True`, black geometry / red padlock).
3. **Quarter-Symmetry + Double Mirror:** Model primary bodies in the **`+Y / +Z` quadrant** first, then execute **2-axis `Mirror`** operations across the **XY** and **XZ** construction planes with `isCombine = True`.
4. **No `Extrude > Intersect`:** Build outer envelopes cleanly and remove material using explicit directional `Cut` extrusions (`participantBodies` targeted).
5. **Single Unified Body:** Join `STEM` and `GUARD` into `HandleBody [KEY]` via `Combine > Join` (`isKeepToolBodies = False`) before applying cross-seam fillets.

---

## 3. Master User Parameters (29 Total)

### Base Parameters (24)
| Parameter | Value | Unit | Description |
| :--- | :--- | :--- | :--- |
| `stem_length` | `33.5` | mm | Total insertion blade length from guard front datum (`22.0 + 6.0 + 5.5`) |
| `stem_width` | `9.5` | mm | Transverse outer width of stem blade |
| `stem_thickness` | `4.1` | mm | Vertical outer thickness of stem rails |
| `stem_edge_rim` | `1.4` | mm | Outer perimeter wall thickness bordering recessed web |
| `stem_cutout_start` | `22.0` | mm | Axial distance from guard face to locking window start |
| `stem_cutout_size` | `6.0` | mm | Square retention locking window dimension (`6.0 × 6.0 mm`) |
| `stem_tip_diamond_len` | `5.5` | mm | Axial length of tip diamond (`X = 28.00` to `33.50 mm`) |
| `stem_notch_start` | `14.0` | mm | Axial distance to concave detent arc start |
| `stem_notch_depth` | `1.0` | mm | Nominal detent depth reference |
| `stem_notch_span` | `4.0` | mm | Axial arc span of concave detent (`X = 14.00` to `18.00 mm`) |
| `stem_notch_taper` | `4.0` | mm | Linear chisel taper from `X = 18.00` to `22.00 mm` |
| `stem_chamfer` | `0.5` | mm | Reserved reference parameter |
| `guard_length` | `3.0` | mm | Axial thickness of stop collar (`X = 0.00` to `-3.00 mm`) |
| `guard_width` | `18.0` | mm | Transverse width of stop collar |
| `guard_height` | `11.0` | mm | Vertical height of stop collar |
| `guard_corner_rad` | `1.5` | mm | Axial corner fillet radius on guard collar |
| `guard_perimeter_rad` | `1.0` | mm | Front and rear outer perimeter fillet radius on guard collar |
| `handle_guard_offset` | `1.75` | mm | Equal shoulder step inset from guard collar on all 4 sides |
| `handle_length` | `24.0` | mm | Axial length of ergonomic grip section (`X = -3.00` to `-27.00 mm`) |
| `handle_width` | `27.0` | mm | Maximum rear transverse width of grip section |
| `handle_height` | `17.0` | mm | Maximum rear vertical thickness of grip section |
| `handle_pocket_depth` | `2.0` | mm | Sloped finger grip pocket depth per face |
| `lanyard_hole_dia` | `9.0` | mm | Through-hole diameter for tether cord or clip |
| `junction_fillet_rad` | `0.25` | mm | Stress-relief fillet at seams, inner web corners, and outer stem rails |

### Formula-Driven Parameters (5)
| Parameter | Expression | Evaluated | Description |
| :--- | :--- | :--- | :--- |
| `stem_internal_width` | `stem_width - (2 * stem_edge_rim)` | `6.70 mm` | Recessed web pocket width |
| `stem_internal_thickness` | `stem_thickness - (2 * stem_edge_rim)` | `1.30 mm` | Recessed web base thickness |
| `stem_tip_diamond_thk` | `stem_thickness` | `4.10 mm` | Peak thickness at `X = 30.75 mm` for single-plane nose |
| `handle_neck_width` | `guard_width - (2 * handle_guard_offset)` | `14.50 mm` | Equal `1.75 mm` inset neck width |
| `handle_min_height` | `guard_height - (2 * handle_guard_offset)` | `7.50 mm` | Equal `1.75 mm` inset neck height |

---

## 4. Component Geometry & Post-Run Refinements

### A. `STEM` (`X = 0.00` to `+33.50 mm`)
- **Outer Blade & Rails:** `9.50 mm` wide (`Y = ±4.75 mm`) × `4.10 mm` thick (`Z = ±2.05 mm`), bordered by `1.40 mm` side rails (`Y = ±3.35` to `±4.75 mm`).
- **Recessed Web & Concave Detent (`Y = -3.35` to `+3.35 mm`):**
  - `X = 0.00` to `14.00 mm`: Flat web at `1.30 mm` thickness (`Z = ±0.65 mm`).
  - `X = 14.00` to `18.00 mm`: 3-point concave detent arc dipping to a `0.60 mm` center bridge (`Z = ±0.30 mm`) at `X = 16.00 mm`, returning to `Z = ±0.65 mm` at `X = 18.00 mm`.
  - `X = 18.00` to `22.00 mm`: Linear double-chisel ramp tapering to `Z = 0` at `X = 22.00 mm`.
- **Locking Window (`X = 22.00` to `28.00 mm`):** Full through-slot `6.00 mm` × `6.00 mm` (`Y = ±3.00 mm`), leaving `1.75 mm` side walls (`Y = ±3.00` to `±4.75 mm`).
- **Diamond Tip & Single-Plane Chisel Nose (`X = 28.00` to `33.50 mm`):**
  - Inner center diamond (`Y = ±3.35 mm`) rises linearly from `Z = 0` at `X = 28.00 mm` to full rail height `Z = ±2.05 mm` at `X = 30.75 mm`, merging seamlessly with the outer side rails.
  - From `X = 30.75` to `33.50 mm`, the entire `9.50 mm` width tapers in a **single uninterrupted flat plane** on top and bottom down to a sharp chisel tip (`Z = 0`) at `X = 33.50 mm`.

### B. `GUARD` (`X = 0.00` to `-3.00 mm`)
- Rectangular stop collar `18.00 mm` (Y) × `11.00 mm` (Z) × `3.00 mm` (X).
- **Corner & Perimeter Fillets:** `1.50 mm` (`guard_corner_rad`) on the 4 axial edges; `1.00 mm` (`guard_perimeter_rad`) on the front (`X = 0.00 mm`) and rear (`X = -3.00 mm`) outer perimeter loops after joining.

### C. `HANDLE` (`X = -3.00` to `-27.00 mm`)
- **Equal Shoulder Offset (`1.75 mm`):** Transitions from the guard with an equal `1.75 mm` step inset on all four sides (`14.50 mm` neck width × `7.50 mm` neck height at `X = -3.00 mm`), flaring linearly to `27.00 mm` width × `17.00 mm` height at the rear butt (`X = -27.00 mm`).
- **Sloped Finger Pockets (Both Faces):** Trapezoidal recessed grip pockets spanning `X = -7.00` to `-24.00 mm`, widening from `11.00 mm` (`Y = ±5.50 mm`) at the front to `22.00 mm` (`Y = ±11.00 mm`) at the rear, cut `2.00 mm` (`handle_pocket_depth`) parallel to the sloped top/bottom faces.
- **Lanyard Hole:** `9.00 mm` (`lanyard_hole_dia`) through-hole centered at `X = -18.60 mm` (`guard_length + handle_length * 0.65`), `Y = 0`, finished with a `0.40 mm` rim fillet on both faces.
- **Handle Edge Rounding:** `2.50 mm` fillet on the 4 rear vertical butt corners; `1.00 mm` perimeter border fillet along the upper and lower handle edges.

### D. Stress-Relief Finishing Fillets (`0.25 mm` `junction_fillet_rad`)
- Applied after `Combine > Join` at:
  1. `STEM`-to-`GUARD` seam (`X = 0.00 mm`)
  2. `GUARD`-to-`HANDLE` neck seam (`X = -3.00 mm`)
  3. Inner stem web/lip pocket transitions (`Y = ±3.35 mm`)
  4. Outer longitudinal stem rail edges (`Y = ±4.75 mm, Z = ±2.05 mm`)
