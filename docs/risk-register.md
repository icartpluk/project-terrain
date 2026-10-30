# Project TERRAIN — Initial risk register
**Status:** Preliminary qualitative risks; ratings require expert review.

| ID | Risk | Consequence | Proposed mitigation | Evidence needed |
|---|---|---|---|---|
| R-01 | Humanoid loses balance on debris | Equipment damage or unsafe motion | Conservative traversal, supervised inert tests | Stability logs |
| R-02 | Communication interrupted | Loss of remote supervision | Independent safe-stop policy | Fault-injection report |
| R-03 | Localization drift | Collision or misnavigation | Uncertainty thresholds and abort behavior | Ground-truth mapping trials |
| R-04 | Unauthorized command | Unsafe actuation | Authentication, least privilege, isolated safety path | Security test report |
| R-05 | Sensor failure or misleading data | Operator makes unsafe decision | Health monitoring, stale-data warnings, safe stop | Sensor fault trials |
| R-06 | Manipulator exceeds stability envelope | Dropped object or tip-over | Payload limits, balance monitoring | Inert handling trials |
| R-07 | Platform unsuitable for hazardous environment | Premature confidence | Explicit qualification gap and independent review | Specialist assessment |
| R-08 | Misrepresentation of simulation as readiness | Unsafe deployment decisions | Stage gates, limitations, peer review | Review signoff |
| R-09 | Intellectual-property or publication misstep | Loss of options or disclosure | Private development and appropriate legal advice | Publication review |
| R-10 | Humanoid is inferior to other robot types | Wasted effort | Benchmark against tracked and wheeled systems | Comparative results |

Risk ownership, likelihood, severity, and residual risk remain **TBD** until reviewed by qualified engineers.
