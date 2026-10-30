# Inert simulation work package

This folder specifies a future **nonhazardous** robotics simulation, not a functioning simulator.

## Proposed structure
- `scenarios/`: abstract tunnel geometry and randomized obstacles
- `configs/`: candidate robot assumptions and fault settings
- `schemas/`: telemetry and trial-result formats
- `reports/`: reproducible results and safety findings

## First implementation task
Choose a simulation engine and verify access to appropriate platform models. Do not assume a Tesla Optimus model or API is publicly available.

## Ground rules
Only inert objects and generic environments. No real nuclear-site layouts or nuclear-material handling workflows.
