# Safety validation gates for the inert TERRAIN simulator

**Status:** Research checklist; not evidence of hardware safety, nuclear-operation readiness, or certification.

## Purpose
Separate what the grid simulator demonstrates from what remains unverified. A green software test is not a real-world safety claim.

## Gate 1 — Deterministic software behavior
- Reproduce every scenario with pinned seed, map, fault placement, and delay settings.
- Verify the baseline, link loss, unauthorized command, and local E-stop on the same maps.
- Exercise first, middle, and final motion-tick faults; count disconnected and after-arrival cases separately.
- Verify the stop latch prevents resumed movement without an explicit fresh simulation reset.
- Require Python and browser-model parity and passing CI on supported platforms.

**Evidence:** Test logs, command line, seed/configuration, and exported per-trial data.

## Gate 2 — Safety property checks
- No unauthorized command may change the authorized route or movement target.
- An E-stop bypasses modeled communications delay.
- A fault remains recorded even when the destination is reached during stopping delay.
- Reports must never call reaching the goal during a fault a safety success.
- No-route and non-injected faults must not be counted as successful stops.
- Validate edge cases: one-step routes, zero delays, maximum supported delays, and faults at route boundaries.

**Evidence:** Independently specified expected outcomes and regression fixtures.

## Gate 3 — Human-facing verification
- Visually inspect the generated HTML in a real browser on desktop and mobile.
- Confirm stop status, cause, and pending delay are readable without relying on color.
- Confirm pause, reset, and map loading cannot misleadingly imply a hardware safety reset.
- Confirm export labels and documentation distinguish abstract ticks/cells from seconds/meters.

**Evidence:** Dated browser/device checklist and screenshots, with failures tracked as issues.

## Gate 4 — Future physical research (not satisfied by this repository)
Any move beyond inert simulation requires an independently reviewed hazard analysis, hardware-specific safety architecture, real sensor/actuator validation, emergency-stop testing, authorized test environment, and qualified safety oversight. No nuclear material or hazardous environment testing is authorized or described here.

## Release decision
A software demonstration may be called **simulation-validated** only when Gates 1–3 have documented evidence and outstanding limitations are disclosed. It must never be labeled **field-ready**, **safe for hazardous recovery**, or **certified** based on grid results. Gate 4 is separate and currently unverified.

## Current limitations
The model has no physical braking, inertia, collision dynamics, packet transport, sensor uncertainty, radiation model, or hardware control. Browser visual rendering has not yet been verified. Existing timing and comparison reports provide model outputs, not measured robot performance.

See [simulation/TIMING.md](../simulation/TIMING.md) and [simulation/README.md](../simulation/README.md).
