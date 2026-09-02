# Donor IPC bench-validation gate

No ECU write feature may be enabled until every item in this gate is completed and recorded.

## Required equipment

- Donor Cadillac ELR IPC or another module exactly matching the XML target and compatibility identifier.
- Current-limited automotive-grade 12–14 V supply with voltage/current logging.
- Correct fused bench harness.
- Known-good SWCAN interface on the specified module/DLC pin.
- Independent recovery path using authorized GM tooling.

## Stage 1 — Identity and passive capture

1. Record module part, hardware, software, calibration, VIN, and configuration identifiers.
2. Confirm diagnostic address, physical layer, bus voltage, bitrate, and addressing.
3. Capture a complete stock startup and diagnostic session without transmitting configuration writes.

## Stage 2 — Complete readback

1. Read every DID referenced by the XML write sequence.
2. Store raw request and response frames, timestamps, adapter identity, and power state.
3. Hash the raw capture and normalized readback JSON.
4. Run `opendps-config compare` and require `readback_coverage.complete=true`.
5. Manually review DTC-mask, security-counter, configuration-complete, VIN, and XML-identity DIDs.

## Stage 3 — Independent calculation check

1. Supply the authoritative vehicle build record/RPO list.
2. Calculate the result with OpenDPS.
3. Calculate the result independently with authorized DPS tooling without executing a write.
4. Require byte-for-byte agreement for every changed DID.
5. Investigate every unmatched field, overlapping rule, missing RPO, and schema warning.

## Stage 4 — Controlled donor write

1. Preserve two verified copies of the complete stock readback.
2. Change one reversible, low-consequence display field only.
3. Use stable power and record the entire transaction.
4. Power-cycle the donor IPC and verify the intended change, DTC state, communication, and recovery.
5. Restore the original payload and verify restoration after another power cycle.

## Release criterion

Write support remains disabled until the test record proves deterministic calculation, complete backup, successful single-field change, successful restoration, and a functioning recovery path. Vehicle-control and safety-system configuration remain outside this tool's initial write scope.
