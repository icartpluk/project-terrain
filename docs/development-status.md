# Development status and next steps

**Reviewed:** 2026-11-01
**Scope:** Inert, offline grid simulation and conceptual engineering only.
**Phase status:** Complete — the current offline simulation, validation, and browser-usability scope is finished. Physical research remains outside this phase and its oversight gate is not satisfied.

## Progress

- Reviewed merged PR #24 and PR #25. They introduced a polished but separate scripted dashboard and documented that it was not connected to the Python simulation.
- Replaced that illustrative dashboard behavior with an embedded, reproducible export from `simulation/sim.py`. The displayed grid, route events, scenario status, move counts, positions and fault outcomes now come directly from the canonical deterministic model.
- Added `presentation/build.py` and regression tests that compare each dashboard scenario against simulator results at early, default and late fault ticks. The browser is a view and playback controller for recorded events; it does not run another planner or inject separate faults.
- Made the operations dashboard the default Windows and command-line launch experience. The previous full-featured replay remains available with `python simulation/start.py --detailed-replay`.
- Preserved the offline model's inert scope and made its status visible in the dashboard, including explicit limits around physical capability, sensors, actuators, stopping performance and certification.

- PR #11 added four validation gates that distinguish deterministic software checks from safety properties, user-facing review, and any future physical research.
- The timing model has regression coverage for all modeled fault types at each motion tick, zero and asymmetric delays, and the maximum supported delays.
- New checks pin expected position, move count, stop cause, stop tick, and handling of arrival during a delayed stop. The same fixture is rerun to check deterministic output.
- Existing CI runs the Python and JavaScript simulation tests on Ubuntu and Windows; the regression matrix passed both before PR #12 merged.
- Desktop and mobile browser checks passed for status text, stop cause, delay phase, keyboard access, and touch controls.
- The limited-view exploration panel also passed a desktop and mobile usability check.
- Deterministic map-file parser checks cover valid-input repeatability, the size boundary, and generated malformed-input cases.
- PR #15 added the limited-observation Python model; PR #17 integrated it into the offline browser demo with deterministic Python/browser parity checks. Ubuntu and Windows checks passed before merge.

## Current limits and unresolved work

- The new presentation dashboard is generated from the simulator's fixed grid and deterministic scenario output. It is a static recorded replay; changing the model requires rebuilding the dashboard with `python presentation/build.py`.
- Its Play, Step and Reset controls only change which already-recorded event is visible; the browser does not create new simulation results.

- The partial-observation experiment is integrated into the offline browser replay as a separate, deterministic scenario. The browser receives only recorded known-map frames, not the hidden map or obstacle schedule; controls are native step and reset buttons.
- The partial-observation scenario uses abstract grid cells and ticks, a fixed observation radius, and a supplied event schedule; it does not model sensor physics, physical obstacle motion, braking, collisions, or hardware.
- Independent safety controls and cybersecurity protections remain conceptual requirements. This repository has no physical safety controller, actuator interface, network command path, or hardware E-stop.
- Seeded reports are reproducible model outputs; they are not measured robot performance or evidence of readiness for hazardous environments.
- Passing software checks validate only the modeled behavior; they do not establish hardware safety.

## Recommended next steps

No further work is pending for the current offline-simulation scope. Any future modeling should stay inert and generic. Physical research would require qualified independent safety, security, and legal oversight; simulator results do not satisfy that gate.

## Release language

The project may describe results as simulation behavior after the relevant software checks pass. Do not describe the simulator as field-ready, certified, or safe for hazardous recovery based on grid results.
