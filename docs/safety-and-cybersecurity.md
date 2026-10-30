# Cybersecurity, independent safety controls, and fault tolerance

These requirements were explicitly added by the project originator.

## Independent safety controller
- Separate safety-critical controls from mission software.
- Provide a tested emergency stop and independent power isolation where appropriate.
- Require safe-stop behavior on sensor disagreement or critical faults.

## Cybersecurity
- Authenticate and authorize all commands.
- Apply least privilege, strong key management, signed software updates, and audit logging.
- Isolate safety functions from external networks and untrusted autonomy components.

## Fault tolerance
- Define safe loss-of-communications behavior.
- Detect degraded sensors, actuator faults, and localization failure.
- Exercise faults in simulation and inert physical testbeds before any hazardous deployment.

## Hazard containment and oversight
- Treat containment as a specialist-designed, independently verified subsystem.
- Require radiation protection, nuclear criticality safety, and regulatory experts for any actual nuclear-material operation.
- Preserve human supervisory authority, explicit mission authorization, and independent abort authority.

## Validation
- Threat modeling and independent security review.
- Fault-injection tests, stop-time measurements, recovery-state testing, and documented hazard analysis.
