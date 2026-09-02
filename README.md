# OpenDPS Config Tool

OpenDPS Config Tool is an independent, offline utility for inspecting and validating GM-style DPS ECU configuration XML files, evaluating their RPO/build-data rules, and generating reviewable DID configuration payloads.

The initial engineering analysis is based on a user-supplied Cadillac ELR instrument-panel-cluster configuration file. The original GM XML is deliberately excluded from the public repository. Place an authorized local copy at `examples/elr_ipc/XMLFile.xml` to reproduce that analysis.

## Current capabilities

- Identify the target ECU, diagnostic address, protocol, physical bus, security metadata, XML part number, and alpha code.
- Inventory DIDs, byte/bit parameters, interpretations, RPO codes, automatic configuration rules, and write order.
- Parse a simple build-record text file containing present RPO codes.
- Evaluate the XML's Boolean RPO expressions (`!`, `&`, `|`, and parentheses).
- Apply matching configuration values to copies of the XML default DID payloads.
- Decode raw DID readbacks into named fields and human-readable interpretations.
- Compare current vehicle data, XML defaults, and RPO-calculated data.
- Preserve unmodeled vehicle bits and generate a change-only plan when readback data is supplied.
- Produce a JSON configuration plan for review.
- Create a deterministic configuration bundle ZIP containing the XML, build record, plan, and manifest.
- Never communicate with or write to a vehicle.

## SPS2 Capture utility

The project also includes a separate Windows utility for preserving files that
SPS2 and Techline Connect create or modify during a normal programming session.
Development is maintained on the
[`feature/sps2-capture`](https://github.com/Voltarians/Open-DPS-Config-Tool/tree/feature/sps2-capture)
branch so the passive capture workflow remains isolated from the archive and
configuration engine until Windows validation is complete.

SPS2 Capture currently provides:

- Automatic discovery of common GM, SPS, and Techline data directories.
- Explicit monitoring of additional cache or log paths supplied by the operator.
- A pre-session baseline inventory.
- Timestamped, immutable copies of every observed file version.
- SHA-256 evidence hashes, an append-only JSONL event log, CSV inventory, and
  machine-readable session manifest.
- A final collection window after the operator stops capture.
- A double-clickable Windows command launcher.

The intended workflow is straightforward:

1. Start SPS2 Capture before opening SPS2 or Techline Connect.
2. Verify every relevant cache and log directory is being watched.
3. Run the SPS2 download or programming session normally.
4. Stop capture only after SPS2 has finished.
5. Preserve the evidence bundle unchanged and give a copy to the archive analyzer.

The program observes ordinary filesystem activity only. It does not decrypt
network traffic, inject into GM software, bypass access controls, alter SPS2, or
communicate with the vehicle. The branch passes the repository test suite, but
it still requires an end-to-end Windows test against the actual SPS2 cache paths
before it should be trusted for a paid programming session.

## Non-goals for the first release

- Circumventing ECU security access.
- Flashing or configuring a vehicle.
- Reproducing GM proprietary Type-4 application DLLs.
- Treating XML defaults as a backup of a vehicle's current configuration.

## GDS2 Capture utility

The [`feature/gds2-capture`](https://github.com/Voltarians/Open-DPS-Config-Tool/tree/feature/gds2-capture)
branch contains a separate passive Windows diagnostic-session capture program.
It preserves GDS2/Techline/VCX/J2534 file changes, process snapshots, pass-through
driver registrations, relevant Windows events, and optional independent CAN-log
files in a hashed evidence bundle. It does not inject into GDS2 or communicate
with the vehicle.

## Quick start

Python 3.10 or later is required. No third-party Python packages are needed.

The integration branch also provides a shared Atlas export path for both capture
programs:

```powershell
python -m atlas_importer CAPTURE-BUNDLE --output ATLAS-IMPORT --vehicle-id volt-test
```

## OBD Atlas and DBC status

The shared importer currently emits `obd-atlas.gm-session.v1` JSON plus artifact
and identifier CSV indexes. As of this branch, the OBD Atlas repository does
**not** yet provide DBC ingestion or DBC generation. This project therefore does
not claim that its JSON/CSV output is a DBC file or that Atlas can consume DBC
without an additional adapter.

The planned DBC boundary is:

- **DBC input:** parse messages, arbitration IDs, signal bit positions, byte
  order, signedness, scaling, offsets, units, value tables, transmitters, and
  receivers while retaining source-file provenance.
- **DBC output:** publish only evidence-backed CAN/CAN FD definitions. Unknown
  signals remain unknown; candidate identifiers are never promoted to confirmed
  signals automatically.
- **Round-trip validation:** reparse every generated DBC and compare its semantic
  message/signal model before release.
- **Network scope:** DBC covers CAN-family frames. LIN requires an LDF-oriented
  path, and diagnostic request/response definitions require a separate schema.

Until that adapter exists, Atlas session JSON/CSV is the authoritative normalized
handoff from SPS2 Capture and GDS2 Capture.

```powershell
python -m opendps_config inspect examples\elr_ipc\XMLFile.xml
python -m opendps_config plan examples\elr_ipc\XMLFile.xml --rpos "EF7,UE1,IO6" --output plan.json
python -m opendps_config bundle examples\elr_ipc\XMLFile.xml --rpos "EF7,UE1,IO6" --output ELR_IPC_config_bundle.zip
```

Decode a DID readback:

```powershell
python -m opendps_config decode examples\elr_ipc\XMLFile.xml --did 00A1 --payload YOUR_HEX_READBACK
```

Compare current data with XML defaults and the RPO-calculated result:

```powershell
python -m opendps_config compare examples\elr_ipc\XMLFile.xml `
  --build-record vehicle-rpos.txt `
  --readback ipc-readback.json `
  --output comparison.json
```

Readback JSON maps DID numbers or XML DID identifiers to complete hexadecimal payloads:

```json
{
  "00A1": "complete payload from the IPC",
  "00A3": "complete payload from the IPC"
}
```

Run the tests:

```powershell
python -m unittest discover -s tests -v
```

## Build-record input

The initial parser accepts comma-separated or whitespace-separated RPO codes. Lines beginning with `#` are comments. Example:

```text
# Example only; use the actual vehicle build record.
EF7 IO6 UE1
```

The parser does not yet claim compatibility with every GM SPS/DPS build-record XML dialect. Raw GM build records should be retained alongside normalized RPO input for traceability.

## Configuration comparison policy

When a current vehicle payload is supplied, OpenDPS uses it as the baseline and changes only fields controlled by matching XML/RPO rules. When readback is missing, the plan clearly marks the affected DID as `xml_default`. A plan with incomplete readback is unsuitable for ECU writing.

## Safety boundary

Generated plans are engineering artifacts, not authorization to write an ECU. Before any future vehicle-write feature is considered, the current DID contents must be read and preserved, a donor/bench IPC must be used, stable power must be supplied, and the result must be compared byte-for-byte with an authoritative DPS result.

## Project layout

- `opendps_config/`: Python CLI and configuration engine
- `examples/elr_ipc/`: derived ELR IPC analysis; the original XML remains local
- `tests/fixtures/`: synthetic XML used by automated tests
- `tests/`: offline unit tests
- `docs/ARCHITECTURE.md`: roadmap and design boundaries
- `docs/BENCH_VALIDATION.md`: mandatory donor-IPC validation gate
- `sps_capture/` on `feature/sps2-capture`: standalone Windows SPS2 capture utility
- `gds2_capture/` on `feature/gds2-capture`: standalone Windows GDS2 capture utility
- `atlas_importer/` on `feature/atlas-session-importer`: shared Atlas normalizer
