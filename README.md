# Project TERRAIN
**Teleoperated Exploration, Recovery Robotics, and Autonomous Infrastructure Navigation**

## Mission
A research and engineering proposal exploring whether modified Tesla Optimus humanoid robots, supported by specialized equipment and qualified human operators, could help recover hazardous nuclear materials from damaged underground facilities in Iran without exposing personnel unnecessarily.

**Status:** Concept proposal; not an operational plan, Tesla affiliation, or demonstrated capability.

## Watch the grid simulation
On Windows, double-click **START-DEMO.bat** after downloading and extracting the repository. Or run `python simulation/start.py` on any platform to generate the operations dashboard at `results/operations-dashboard.html` and open it in your browser. Python 3.11 or newer is required to generate it; the resulting HTML file opens on its own without Python. For the full-featured replay with seeded maps, map editing and limited-view exploration, run `python simulation/start.py --detailed-replay`. See [local run instructions and controls](simulation/README.md). No third-party packages are required.

The detailed replay includes a limited-view exploration panel. It advances through deterministic, precomputed observation frames, marks unseen cells with `?`, and uses abstract grid cells and a scripted map change. It does not model real sensors, physical obstacle motion, or robot control.

## Operations dashboard

The default launcher uses [`presentation/index.html`](presentation/index.html), a responsive operations dashboard generated from the deterministic Python model. The browser displays recorded results and does not plan routes or invent fault behavior. Rebuild the checked-in page after changing the simulator with `python presentation/build.py`. The dashboard remains an inert software demonstration: it does not model hardware capability, sensors, actuators, physical stopping, or safety certification.

## Project documents
- [Original proposal — preserved wording](docs/original-proposal.md)
- [Mission and feasibility](docs/mission-and-feasibility.md)
- [Robotic system requirements](docs/robotics-requirements.md)
- [Independent safety and cybersecurity](docs/safety-and-cybersecurity.md)
- [Simulation and validation plan](docs/simulation-plan.md)
- [Safety validation gates](docs/safety-validation-gates.md)
- [Development status and next steps](docs/development-status.md)

## Scope and safeguards
The project is limited to conceptual design, safety engineering, simulation, and controlled demonstrations. Any real nuclear-material recovery would require authorization, nuclear-safety specialists, radiation protection, physical security, and applicable international and domestic legal compliance. The project does not provide procedures for accessing, extracting, transporting, or processing nuclear material.

## Long-term application
Technology proven in safe terrestrial testbeds could inform robotic excavation and infrastructure preparation for Mars.

## Attribution
Concept developed through discussions with the project originator; technical assumptions require independent verification.
