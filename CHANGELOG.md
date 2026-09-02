# Changelog

## Atlas Session Importer branch

- Combine SPS2 Capture and GDS2 Capture on one integration branch.
- Add privacy-preserving Atlas JSON/CSV normalization, SHA-256 verification,
  exact deduplication, artifact classification, and candidate identifiers.

## GDS2 Capture branch

- Add a separate passive Windows GDS2 diagnostic-session capture utility.
- Preserve file versions, process state, J2534 registration metadata, relevant
  Windows events, optional CAN-log files, and SHA-256 manifests.

## 0.1.0 — 2026-09-02

- Added GM-style ECU configuration XML inspection.
- Added safe Boolean RPO-expression evaluation.
- Added offline DID-payload planning from XML defaults.
- Added deterministic engineering-bundle creation.
- Added Cadillac ELR IPC reference XML and complete extracted analysis.
- Added five offline unit tests.

## Unreleased

- Added raw DID readback decoding.
- Added vehicle/default/RPO three-way comparison.
- Added change-only plans based on preserved vehicle data.
- Added normalized build-record and readback examples.
- Added GitHub Actions and expanded the suite to seven tests.
- Added a donor-IPC bench-validation gate.
