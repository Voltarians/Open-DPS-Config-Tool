# OpenDPS Config Tool

OpenDPS Config Tool is an independent, offline utility for inspecting and validating GM-style DPS ECU configuration XML files, evaluating their RPO/build-data rules, and generating reviewable DID configuration payloads.

The initial engineering analysis is based on a user-supplied Cadillac ELR instrument-panel-cluster configuration file. The original GM XML is deliberately excluded from the public repository. Place an authorized local copy at `examples/elr_ipc/XMLFile.xml` to reproduce that analysis.

## Current capabilities

- Identify the target ECU, diagnostic address, protocol, physical bus, security metadata, XML part number, and alpha code.
- Inventory DIDs, byte/bit parameters, interpretations, RPO codes, automatic configuration rules, and write order.
- Parse a simple build-record text file containing present RPO codes.
- Evaluate the XML's Boolean RPO expressions (`!`, `&`, `|`, and parentheses).
- Apply matching configuration values to copies of the XML default DID payloads.
- Produce a JSON configuration plan for review.
- Create a deterministic configuration bundle ZIP containing the XML, build record, plan, and manifest.
- Never communicate with or write to a vehicle.

## Non-goals for the first release

- Circumventing ECU security access.
- Flashing or configuring a vehicle.
- Reproducing GM proprietary Type-4 application DLLs.
- Treating XML defaults as a backup of a vehicle's current configuration.

## Quick start

Python 3.10 or later is required. No third-party Python packages are needed.

```powershell
python -m opendps_config inspect examples\elr_ipc\XMLFile.xml
python -m opendps_config plan examples\elr_ipc\XMLFile.xml --rpos "EF7,UE1,IO6" --output plan.json
python -m opendps_config bundle examples\elr_ipc\XMLFile.xml --rpos "EF7,UE1,IO6" --output ELR_IPC_config_bundle.zip
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

## Safety boundary

Generated plans are engineering artifacts, not authorization to write an ECU. Before any future vehicle-write feature is considered, the current DID contents must be read and preserved, a donor/bench IPC must be used, stable power must be supplied, and the result must be compared byte-for-byte with an authoritative DPS result.

## Project layout

- `opendps_config/`: Python CLI and configuration engine
- `examples/elr_ipc/`: derived ELR IPC analysis; the original XML remains local
- `tests/fixtures/`: synthetic XML used by automated tests
- `tests/`: offline unit tests
- `docs/ARCHITECTURE.md`: roadmap and design boundaries
