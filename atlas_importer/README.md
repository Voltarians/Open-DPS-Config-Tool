# GM Session Importer for OBD Atlas

This shared importer accepts completed SPS2 Capture or GDS2 Capture evidence
directories and ZIP files. It validates captured artifact hashes, removes exact
duplicates, classifies artifacts, identifies conservative filename candidates,
and writes Atlas-oriented JSON and CSV indexes.

The importer never modifies the source evidence bundle.

## Usage

```powershell
python -m atlas_importer C:\Users\Monroe\Desktop\GDS2-Captures\GDS2-SESSION `
  --output C:\Users\Monroe\Desktop\Atlas-Import `
  --vehicle-id volt-2013-test
```

ZIP input is also supported. Output contains:

- `atlas-session.json`
- `atlas-artifacts.csv`
- `atlas-identifiers.csv`

DBC is not currently an output format. The present OBD Atlas branches contain
no DBC reader or writer, so this importer deliberately stops at normalized
JSON/CSV. A future DBC adapter must preserve provenance, distinguish candidates
from confirmed signals, and pass semantic round-trip validation.

## Privacy defaults

The normalized output excludes the captured Windows username, computer name,
and original paths. A one-way SHA-256 value permits source-path correlation
without disclosing the path. `--include-paths` is available for strictly local
engineering use, but exported data should be reviewed before sharing.

Use a shop-local vehicle alias with `--vehicle-id`; do not use the VIN unless
the data-governance policy specifically requires it.

## Interpretation boundary

Filename matches are labeled as candidates, not confirmed DIDs or calibration
numbers. Confirmed semantic extraction requires format-specific parsers and
correlation with diagnostic traffic. The importer will not invent those facts.
