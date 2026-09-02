# Atlas session-import contract

The integration branch combines SPS2 Capture, GDS2 Capture, and one shared
normalizer. Both capture programs remain evidence producers; neither writes
directly into the Atlas knowledge base.

## Contract

- Accepted schemas: `opendps.sps-capture.v1` and `opendps.gds2-capture.v1`.
- Output schema: `obd-atlas.gm-session.v1`.
- Evidence input is read-only.
- Artifact bytes are verified against declared SHA-256 values.
- Exact duplicate hashes collapse to one artifact with an observation count.
- Personal workstation fields and paths are excluded by default.
- Candidate identifiers remain explicitly unconfirmed.

Atlas ingestion should retain the normalized session's source-manifest hash so
every record can be traced back to a specific preserved evidence bundle.

## DBC boundary

DBC import/export is not implemented in the current OBD Atlas repository or in
this integration branch. It is a downstream adapter concern. DBC output must be
limited to confirmed CAN/CAN FD message and signal definitions and must be
reparsed for semantic comparison before distribution. LIN descriptions belong
in an LDF-compatible path rather than being forced into DBC.
