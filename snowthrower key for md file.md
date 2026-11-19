# CAD AI BENCHMARK CHALLENGE (V5 FINAL): Parametric Snowthrower Ignition Key (`STKey_V5`)

## Objective & Evaluation Criteria
Build a 100% parametric, watertight manifold 3D solid model of a push-in snowthrower ignition key (`HandleBody [KEY]`) in **Autodesk Fusion 360** (`Parametric Design Mode`, `Units: mm`) using the Fusion 360 Python API or live MCP/Add-In commands.

### Mandatory Modeling Rules (Graded Pass/Fail):
1. **NO Boolean Intersect (`IntersectFeatureOperation`):** Do **NOT** extrude oversized bounding boxes and intersect them. Build all geometry directly from true finished profiles using `NewBody`, `Join`, and `Cut`.
2. **Quarter-Model (`1/4` Quadrant) + Two-Axis Mirror (`XY` & `XZ`):** Because the key is bilaterally symmetrical across `XY` (`Z = 0`) and `XZ` (`Y = 0`), model **only the `+Y / +Z` quadrant** (`Y >= 0, Z >= 0`) for `STEM`, `GUARD`, and `HANDLE`, apply local pockets and quadrant corner fillets, and mirror across `XY` (`Z = 0`) and `XZ` (`Y = 0`) for a clean ~22-feature timeline.
3. **All 29 User Parameters Active & Linked:** Every dimension must be driven by the User Parameter expressions in the table below (no hardcoded magic numbers in features).
4. **100% Fully Constrained Sketches & Zero Timeline Warnings:** Every sketch must report `isFullyConstrained == True` (red padlock icon), and every timeline feature must compute cleanly with zero yellow/red warnings.

---

## Coordinate System & Datum Origin `(0, 0, 0)`
* **Origin `(0, 0, 0)`:** Centered at the **front face of the Guard collar** (`YZ` plane, `X = 0.00 mm`), on the horizontal (`Y = 0`) and vertical (`Z = 0`) symmetry centerlines.
* **`+X` (`0.00` to `+33.50 mm`):** Insertion blade (`STEM`) extending to the single-plane chisel nose tip (`X = +33.50 mm, Z = 0`).
* **`-X` (`0.00` to `-27.00 mm`):** Stop collar (`GUARD`, `X = 0` to `-3.00 mm`) and ergonomic grip (`HANDLE`, `X = -3.00` to `-27.00 mm`).

---

## Complete User Parameter Table (29 Parameters)

| Parameter Name | Expression / Value | Unit | Engineering Function |
| :--- | :--- | :--- | :--- |
| `stem_length` | `33.50` | mm | Total insertion blade length from guard front datum |
| `stem_width` | `9.50` | mm | Transverse outer width of stem blade (`Y = ±4.75 mm`) |
| `stem_thickness` | `4.10` | mm | Vertical outer thickness of stem rails (`Z = ±2.05 mm`) |
| `stem_edge_rim` | `1.40` | mm | Outer perimeter wall thickness bordering recessed web |
| `stem_internal_width` | `stem_width - (2 * stem_edge_rim)` | mm | Recessed web pocket width (`6.70 mm`, `Y = ±3.35 mm`) |
| `stem_internal_thickness` | `stem_thickness - (2 * stem_edge_rim)` | mm | Recessed web base thickness (`1.30 mm`, `Z = ±0.65 mm`) |
| `stem_cutout_start` | `22.00` | mm | Axial distance from guard face to locking window start |
| `stem_cutout_size` | `6.00` | mm | Square retention locking window dimension (`6.00 x 6.00 mm`) |
| `stem_tip_diamond_len` | `5.50` | mm | Axial length of tip diamond (`X = 28.00` to `33.50 mm`) |
| `stem_tip_diamond_thk` | `stem_thickness` | mm | Peak thickness at `X = 30.75 mm` (`4.10 mm`, `Z = ±2.05 mm`) |
| `stem_notch_start` | `14.00` | mm | Axial distance to concave detent arc start |
| `stem_notch_depth` | `1.00` | mm | Nominal detent reference (valley at `Z = ±0.30 mm`) |
| `stem_notch_span` | `4.00` | mm | Axial arc span of concave detent (`X = 14.00` to `18.00 mm`) |
| `stem_notch_taper` | `4.00` | mm | Linear chisel taper from `X = 18.00` to `22.00 mm` |
| `stem_chamfer` | `0.50` | mm | Reserved reference parameter |
| `guard_length` | `3.00` | mm | Axial thickness of stop collar (`X = 0` to `-3.00 mm`) |
| `guard_width` | `18.00` | mm | Transverse width of stop collar (`Y = ±9.00 mm`) |
| `guard_height` | `11.00` | mm | Vertical height of stop collar (`Z = ±5.50 mm`) |
| `guard_corner_rad` | `1.50` | mm | Axial corner fillet radius on guard collar |
| `guard_perimeter_rad` | `1.00` | mm | Front and rear outer perimeter fillet radius on guard collar |
| `handle_guard_offset` | `1.75` | mm | Equal shoulder step inset from guard collar on all 4 sides |
| `handle_length` | `24.00` | mm | Axial length of ergonomic grip (`X = -3.00` to `-27.00 mm`) |
| `handle_width` | `27.00` | mm | Maximum rear transverse width of grip (`Y = ±13.50 mm`) |
| `handle_neck_width` | `guard_width - (2 * handle_guard_offset)` | mm | Tapered neck width at guard rear face (`14.50 mm`, `Y = ±7.25 mm`) |
| `handle_height` | `17.00` | mm | Maximum rear vertical thickness of grip (`Z = ±8.50 mm`) |
| `handle_min_height` | `guard_height - (2 * handle_guard_offset)` | mm | Tapered vertical thickness at guard rear face (`7.50 mm`, `Z = ±3.75 mm`) |
| `handle_pocket_depth` | `2.00` | mm | Sloped finger grip pocket depth per face |
| `lanyard_hole_dia` | `9.00` | mm | Through-hole diameter centered at `X = -18.60 mm, Y = 0` |
| `junction_fillet_rad` | `0.25` | mm | Stress-relief fillet at component seams, inner web corners, and outer stem rails |

---

## Detailed Component Geometry (`+Y / +Z` Quadrant -> Double Mirror)

### 1. Component `STEM` (`X = 0.00` to `+33.50 mm`)
* **Base Blade (`StemSize` on `XY`):** Quadrant rectangle `(0, 0)` to `(33.50, 4.75)` with the `6.00 x 6.00 mm` locking window quadrant cutout (`X = 22.00` to `28.00 mm`, `Y = 0` to `3.00 mm`). Extrude along `+Z` by `stem_thickness / 2` (`2.05 mm`).
* **Web, Concave Detent, Double-Chisel Window & Single-Plane Nose (`StemCuts` on `XZ`):**
  1. **Recessed Web (`X = 0` to `14.00 mm`):** Cut across `stem_internal_width / 2` (`3.35 mm`) down to `Z = 0.65 mm` (`stem_internal_thickness / 2`), leaving a `1.40 mm` (`stem_edge_rim`) outer side rail.
  2. **Concave Detent (`X = 14.00` to `18.00 mm`):** A **concave 3-point arc** curving **inward toward `Z = 0`** to a minimum height of `Z = 0.30 mm` at `X = 16.00 mm` (`0.60 mm` full bridge after mirroring) and returning to `Z = 0.65 mm` at `X = 18.00 mm`.
  3. **Front Chisel Taper (`X = 18.00` to `22.00 mm`):** Linear taper from `Z = 0.65 mm` at `X = 18.00 mm` down to a sharp chisel edge at `Z = 0` at `X = 22.00 mm`.
  4. **Full Window Clearance (`X = 22.00` to `28.00 mm`):** Cut all the way to `Z = 0` across the full `3.35 mm` (`stem_internal_width / 2`) pocket width so **zero protruding ledges** remain inside the `6.00 mm` window walls.
  5. **Inner Tip Diamond (`X = 28.00` to `30.75 mm`):** Cut across `stem_internal_width / 2` (`3.35 mm`) starting from `Z = 0` at `X = 28.00 mm` and rising linearly to `Z = 2.05 mm` (`stem_tip_diamond_thk / 2`) at `X = 30.75 mm`, meeting the outer `1.40 mm` side rail flush.
  6. **Full-Width Single-Plane Nose Slope (`X = 30.75` to `33.50 mm`):** Cut across the **full quadrant width `stem_width / 2` (`4.75 mm`)** sloping linearly from `Z = 2.05 mm` at `X = 30.75 mm` down to `Z = 0` at `X = 33.50 mm` as one continuous flat surface.

### 2. Component `GUARD` (`X = 0.00` to `-3.00 mm`)
* **Collar Quadrant (`GuardSize` on `YZ`):** Rectangle `(0, 0)` to `(9.00, 5.50)` extruded `-3.00 mm` (`-guard_length`) along `-X`, with a `1.50 mm` (`guard_corner_rad`) fillet on the outer axial corner `(Y = 9.00, Z = 5.50)`.

### 3. Component `HANDLE` (`X = -3.00` to `-27.00 mm`)
* **Tapered Grip Quadrant (`SideCut` on `XZ` + `TopCutSketch` on `XY`):** Extrude quadrant profile (`X = -3.00 mm, Z = 3.75 mm` to `X = -27.00 mm, Z = 8.50 mm`) along `+Y` by `handle_width / 2` (`13.50 mm`), trim the outer plan wedge (`X = -3.00 mm, Y = 7.25 mm` to `X = -27.00 mm, Y = 13.50 mm`) via `Cut`, and apply a `2.50 mm` fillet to the rear vertical corner `(X = -27.00, Y = 13.50)`.
* **Sloped Finger Pocket (`PocketPlan` on `XY`):** Trapezoidal quadrant pocket (`X = -7.00 mm, Y = 0..5.50 mm` to `X = -24.00 mm, Y = 0..11.00 mm`) offset-cut `2.00 mm` (`handle_pocket_depth`) parallel to the slanted top handle face.

### 4. Two-Axis Mirror (`XY` & `XZ`), Lanyard Hole, Combine & Finishing Fillets
1. Mirror `STEM`, `GUARD`, and `HANDLE` quadrants across `XY` (`Z = 0`) and `XZ` (`Y = 0`) to form full symmetric bodies.
2. Cut the `9.00 mm` (`lanyard_hole_dia`) through-hole centered at `X = -18.60 mm, Y = 0` and apply a `0.40 mm` rim fillet.
3. Combine (`Join`) `STEM` and `GUARD` into `HandleBody [KEY]`.
4. Apply finishing fillets:
   * **`1.00 mm` (`guard_perimeter_rad`)** around the front (`X = 0`) and rear (`X = -3.00 mm`) outer perimeter loops of the guard collar.
   * **`1.00 mm`** around the 10 outer grip border edges of the handle (excluding the guard joint and finger pocket interior).
   * **`0.25 mm` (`junction_fillet_rad`)** stress-relief fillets along: (a) the `STEM`–`GUARD` and `GUARD`–`HANDLE` interface seams, (b) the inner `90°` longitudinal pocket roots and top inner rail lips of `STEM`, and (c) the 4 outer longitudinal edges of `STEM` (`Y = ±4.75 mm, Z = ±2.05 mm` from `X = 0` to `30.75 mm`).
