# Development status and next steps

**Reviewed:** 2026-10-31  
**Scope:** Inert, offline grid simulation and conceptual engineering only.

## Progress

- PR #11 added four validation gates that distinguish deterministic software checks from safety properties, user-facing review, and any future physical research.
- The timing model has regression coverage for all modeled fault types at each motion tick, zero and asymmetric delays, and the maximum supported delays.
- New checks pin expected position, move count, stop cause, stop tick, and handling of arrival during a delayed stop. The same fixture is rerun to check deterministic output.
- Existing CI runs the Python and JavaScript simulation tests on Ubuntu and Windows.

## Current limits and unresolved work

- Browser rendering has not been visually verified on desktop and mobile; automated controller tests do not verify layout, readability, or touch behavior.
- The model uses abstract grid cells and ticks. It does not model braking, inertia, collisions, sensors, localization error, packet transport, or hardware.
- Independent safety controls and cybersecurity protections remain conceptual requirements. This repository has no physical safety controller, actuator interface, network command path, or hardware E-stop.
- Seeded reports are reproducible model outputs; they are not measured robot performance or evidence of readiness for hazardous environments.
- The PR test matrix still needs to pass CI before its coverage can be treated as validated.

## Recommended next steps

1. Review the new regression matrix and require green Ubuntu and Windows checks before merging.
2. Complete and record a desktop and mobile browser checklist for status text, stop cause, delay phase, keyboard access, and touch controls. Track any failures as issues.
3. Add deterministic map-file parsing and malformed-input property cases if editor or save/load behavior changes.
4. Keep future modeling work inert and generic. Any move toward physical research would require qualified independent safety, security, and legal oversight; simulator results do not satisfy that gate.

## Release language

The project may describe results as simulation behavior after the relevant software checks pass. Do not describe the simulator as field-ready, certified, or safe for hazardous recovery based on grid results.
