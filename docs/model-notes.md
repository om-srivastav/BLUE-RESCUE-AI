# Deterministic demo risk and routing model

All numbers in Chunk 2 are **bundled simulated demonstration data**, not measurements. `scripts/generate_demo_grid.py` deterministically generates the 24 × 36 bathymetry and ocean grids in `demo-data` and three fictional hazard annotations. Grid coordinates are row/column indices and are **not geographic coordinates**. The modeled grid scale is 50 m per orthogonal cell; a diagonal step is `50 × √2` m. These are not GPS-derived distances.

## Risk

For each cell, normalized component scores are clamped to `[0, 1]` and combined as:

`total = 0.40 hazard + 0.20 depth + 0.15 wave + 0.15 current + 0.10 uncertainty`.

Weights are configurable and validated to sum to 1. Hazard contribution is `severity × confidence × max(0, 1 − distance/radius)` in grid cells, summed and clamped. Thus influence declines linearly to zero at its radius. Uncertainty uses `1 − confidence` for identified hazards and the annotation's anomaly score for an unknown anomaly; it is not calibrated probability.

The demo's **SIMULATED_OPERATIONAL_DEPTH_THRESHOLD** is 4.5 m. Shallower cells are blocked. Navigable depth risk is `clamp((9.5 − depth)/(9.5 − 4.5))`, so risk approaches zero by 9.5 m. These values are academic scenario parameters, not a real vessel draft or hydrographic clearance.

Wave risk is `clamp((wave_height − 0.4)/(2.0 − 0.4))`; meters are used throughout. These thresholds are demonstration choices, not certified operating limits. Map-cell current risk uses half the current-vector magnitude relative to a 1 m/s reference. `u` is eastward and `v` northward.

For routing movement, a normalized step direction `(dc, −dr)` is compared with the current vector `(u,v)`. Directional current risk is `clamp((|current| / reference_speed) × (1 − dot(normalized vectors))/2)`. Assisting flow therefore has less penalty than cross flow, and opposing flow has more. The route step substitutes this heading-aware score for the neutral current score already in `total`, avoiding double counting. This is simplified academic routing logic, not a vessel hydrodynamics model.

## A* routing

Both routes use 8-way A* with Euclidean distance as an admissible heuristic. Diagonals cannot cut between blocked neighbors. Shortest-route step cost is grid step length (1 or √2). Lower modeled-risk step cost is `step_length × (1 + aggressiveness × heading_aware_risk)` with default aggressiveness 4. This factor is configurable and nonnegative; at zero the objectives choose the same geometry. Paths respect blocked cells. The risk-aware objective trades modeled distance for modeled risk; it does not certify navigation safety.

Route distance sums physical modeled step lengths. Average modeled risk is the arithmetic mean of per-step heading-aware risk; accumulated modeled risk sums it. Minimum depth, hazards whose influence radius the path enters, wave exposure, and directional-current penalty are derived from the computed path. The comparison explanation reports actual route statistics and any factors demonstrably reduced by the alternative path.

## Hazard lifecycle and impact

The three fictional annotations are stored in SQLite with fixed IDs and preserve their original numeric severity factors (`1.00`, `0.70`, `0.65`) so the Chunk 2 baseline remains unchanged. Their source is `DEMO_ANNOTATION`. Manual records use `MANUAL` source and controlled types `WRECKAGE`, `DEBRIS`, `SUBMERGED_OBSTRUCTION`, `KNOWN_INFRASTRUCTURE`, `UNKNOWN_ANOMALY`, or `OTHER`.

Manual severity maps to academic model factors: `LOW=0.35`, `MEDIUM=0.60`, `HIGH=0.82`, `CRITICAL=1.00`. A manual hazard has a five-cell influence radius. Its confidence is an operator-entered certainty between 0 and 1, **not ML confidence**. These values are scenario choices, not maritime regulatory thresholds. Source does not alter the hazard-risk equation; an `UNKNOWN_ANOMALY` also enters the uncertainty component using its anomaly score or, if absent, `1 − confidence`. Only `ACTIVE` hazards enter risk and route calculations. `RESOLVED` hazards remain in SQLite for review.

When a hazard changes, the service recomputes the grid and any latest route plan with its stored endpoints and options. A previous lower modeled-risk route is marked affected when its maximum added/removed weighted hazard contribution reaches at least `0.02`; `route_changed` separately compares old and new coordinate sequences. The response includes previous route metrics, new route metrics, and the old geometry's modeled average risk under the updated field. This separates the effect of the changed risk field from the A* choice; a newly added hazard can raise absolute risk even when rerouting reduces exposure relative to retaining the old path. The comparison is a deterministic academic model, not a safety determination.

## Offline image baselines

Satellite `ClassicalChangeDetector` converts images to grayscale, computes absolute difference, applies a 5×5 Gaussian blur, thresholds at intensity 30, and applies 3×3 morphological open/close. Nonzero mask pixels determine percent change; contours of at least 20 square pixels produce bounding regions. Both images must have identical dimensions. These hand-set values are illustrative; the detector does not distinguish seasonal change, misregistration, shadows, damage, or vessel activity.

Bundled sonar frames have explicit fictional `DEMO_ANNOTATION` boxes. They are not detector predictions. The uploaded-image `HeuristicAnomalyDetector` blurs grayscale pixels, thresholds intensity 185, and reports bright connected contours at least 25 square pixels as `Unknown anomaly`, with an area-based score. This score is not calibrated confidence or an object class. The ML classes raise `MODEL_NOT_CONFIGURED`; no weights, training, or evaluation are present.
