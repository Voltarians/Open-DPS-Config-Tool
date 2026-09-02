# Architecture and roadmap

## Product boundary

OpenDPS Config Tool operates on configuration artifacts. The configuration engine is deliberately separated from any future diagnostic transport. Release 0.1 cannot transmit a CAN frame or write an ECU.

## Pipeline

1. Parse and structurally validate the ECU configuration XML.
2. Normalize build-record RPO content.
3. Evaluate the XML's Boolean `AutoGenExpression` rules.
4. Apply selected values to copies of the XML default DID payloads.
5. Emit a human- and machine-reviewable plan with hashes and warnings.
6. Package the source inputs, plan, and manifest into a deterministic ZIP.

## Next releases

### 0.2 — Schema and comparison

- Validate against the matching DPS XSD set.
- Parse known GM build-record text and XML variants without discarding source data.
- Decode an IPC DID readback against parameter definitions.
- Compare vehicle-read, XML-default, and RPO-calculated payloads.
- Generate a change-only plan with collision and range checks.

### 0.3 — Archive laboratory

- Inventory existing DPS/SPAT and Type-4 ZIP structures.
- Identify package type without executing DLLs.
- Validate filenames, manifests, checksums, references, and required companions.
- Build an open configuration bundle format; do not mislabel it as a proprietary Type-4 archive.

### 0.4 — Bench transport, separately gated

- Read-only GMW3110/UDS inventory through an approved adapter.
- Capture raw requests, responses, timing, and hashes.
- No security bypass and no write support by default.
- Any write-capable implementation requires explicit bench mode, preserved backups, allowlisted DIDs, stable-power validation, and a separate authorization gate.

