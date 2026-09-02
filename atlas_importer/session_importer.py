"""Normalize SPS2 and GDS2 evidence bundles for OBD Atlas ingestion."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import tempfile
import zipfile
from pathlib import Path, PureWindowsPath
from typing import Any

SUPPORTED_SCHEMAS = {
    "opendps.sps-capture.v1": "sps2",
    "opendps.gds2-capture.v1": "gds2",
}

CLASSIFIERS = (
    ("xml", {".xml", ".xsd"}),
    ("diagnostic_log", {".log", ".trace", ".trc", ".txt"}),
    ("can_log", {".asc", ".blf", ".candump", ".pcap", ".pcapng"}),
    ("table", {".csv", ".tsv"}),
    ("structured_data", {".json", ".jsonl", ".yaml", ".yml"}),
    ("database", {".db", ".sqlite", ".sqlite3"}),
    ("calibration_candidate", {".bin", ".cal", ".s19", ".hex", ".mot"}),
    ("archive", {".zip", ".7z", ".rar", ".tar", ".gz"}),
)

IDENTIFIER_PATTERNS = {
    "did_candidate": re.compile(r"(?i)(?:did[_-]?)?\b(?:0x)?([0-9a-f]{4})\b"),
    "gm_part_candidate": re.compile(r"\b([1-9][0-9]{7})\b"),
    "calibration_candidate": re.compile(r"(?i)\b([0-9a-f]{8,16})\b"),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def classify(name: str) -> str:
    suffix = Path(name).suffix.lower()
    for label, suffixes in CLASSIFIERS:
        if suffix in suffixes:
            return label
    return "unclassified"


def source_path_hash(source_path: str) -> str:
    return hashlib.sha256(source_path.encode("utf-8", errors="replace")).hexdigest()


def extract_filename_identifiers(filename: str) -> list[dict[str, str]]:
    output: list[dict[str, str]] = []
    stem = Path(filename).stem
    seen: set[tuple[str, str]] = set()
    for kind, pattern in IDENTIFIER_PATTERNS.items():
        for match in pattern.finditer(stem):
            value = match.group(1).upper()
            key = (kind, value)
            if key not in seen:
                output.append({"kind": kind, "value": value, "basis": "filename"})
                seen.add(key)
    return output


def safe_extract(archive: Path, destination: Path) -> Path:
    with zipfile.ZipFile(archive) as bundle:
        root = destination.resolve()
        for member in bundle.infolist():
            target = (destination / member.filename).resolve()
            if target != root and root not in target.parents:
                raise ValueError(f"Unsafe ZIP member: {member.filename}")
        bundle.extractall(destination)
    manifests = list(destination.rglob("manifest.json"))
    if len(manifests) != 1:
        raise ValueError("Bundle ZIP must contain exactly one manifest.json")
    return manifests[0].parent


def load_bundle_root(path: Path, temporary: Path | None = None) -> Path:
    if path.is_dir():
        return path
    if path.is_file() and path.suffix.lower() == ".zip":
        if temporary is None:
            raise ValueError("ZIP import requires a temporary directory")
        return safe_extract(path, temporary)
    raise ValueError("Input must be a capture directory or ZIP file")


def normalize_artifacts(
    root: Path, manifest: dict[str, Any], include_paths: bool
) -> tuple[list[dict[str, Any]], list[dict[str, str]], list[str]]:
    artifacts: list[dict[str, Any]] = []
    identifiers: list[dict[str, str]] = []
    warnings: list[str] = []
    by_hash: dict[str, dict[str, Any]] = {}

    for index, item in enumerate(manifest.get("files", []), start=1):
        evidence_path = str(item.get("evidence_path", ""))
        source_path = str(item.get("source_path", ""))
        filename = PureWindowsPath(source_path or evidence_path).name
        declared_hash = str(item.get("sha256", "")).lower()
        evidence_file = root / "evidence" / Path(evidence_path.replace("\\", "/"))
        hash_status = "missing"
        if evidence_file.is_file():
            actual_hash = sha256_file(evidence_file)
            hash_status = "verified" if actual_hash == declared_hash else "mismatch"
            if hash_status == "mismatch":
                warnings.append(f"SHA-256 mismatch for artifact {index}: {filename}")
        else:
            warnings.append(f"Evidence file missing for artifact {index}: {filename}")

        if declared_hash and declared_hash in by_hash:
            by_hash[declared_hash]["observations"] += 1
            continue

        record: dict[str, Any] = {
            "artifact_id": f"artifact-{len(artifacts) + 1:06d}",
            "filename": filename,
            "classification": classify(filename),
            "size_bytes": item.get("size_bytes"),
            "sha256": declared_hash,
            "hash_status": hash_status,
            "captured_utc": item.get("captured_utc"),
            "reason": item.get("reason"),
            "source_path_sha256": source_path_hash(source_path),
            "observations": 1,
        }
        if include_paths:
            record["source_path"] = source_path
            record["evidence_path"] = evidence_path
        artifacts.append(record)
        if declared_hash:
            by_hash[declared_hash] = record
        for identifier in extract_filename_identifiers(filename):
            identifiers.append({"artifact_id": record["artifact_id"], **identifier})

    return artifacts, identifiers, warnings


def import_bundle(
    input_path: Path,
    output_dir: Path,
    vehicle_id: str | None = None,
    include_paths: bool = False,
) -> dict[str, Any]:
    input_path = input_path.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="opendps-atlas-") as temp_name:
        root = load_bundle_root(input_path, Path(temp_name))
        manifest_path = root / "manifest.json"
        if not manifest_path.is_file():
            raise ValueError("Capture bundle has no manifest.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        schema = manifest.get("schema")
        if schema not in SUPPORTED_SCHEMAS:
            raise ValueError(f"Unsupported capture schema: {schema!r}")

        artifacts, identifiers, warnings = normalize_artifacts(root, manifest, include_paths)
        session_id = str(manifest.get("session") or manifest_path.parent.name)
        normalized = {
            "schema": "obd-atlas.gm-session.v1",
            "session": {
                "session_id": session_id,
                "source": SUPPORTED_SCHEMAS[schema],
                "source_schema": schema,
                "vehicle_id": vehicle_id,
                "started_utc": manifest.get("started_utc"),
                "stopped_utc": manifest.get("stopped_utc"),
                "source_manifest_sha256": sha256_file(manifest_path),
                "artifact_count": len(artifacts),
                "identifier_count": len(identifiers),
                "paths_included": include_paths,
            },
            "artifacts": artifacts,
            "identifier_candidates": identifiers,
            "warnings": warnings,
        }

    json_path = output_dir / "atlas-session.json"
    json_path.write_text(json.dumps(normalized, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    write_csv(output_dir / "atlas-artifacts.csv", artifacts)
    write_csv(output_dir / "atlas-identifiers.csv", identifiers)
    return normalized


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields: list[str] = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="SPS2/GDS2 capture directory or ZIP")
    parser.add_argument("--output", type=Path, required=True, help="Atlas export directory")
    parser.add_argument("--vehicle-id", help="Local vehicle alias; VIN is discouraged")
    parser.add_argument(
        "--include-paths",
        action="store_true",
        help="Include original/evidence paths; may expose Windows usernames",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = import_bundle(args.input, args.output, args.vehicle_id, args.include_paths)
    print(json.dumps(result["session"], indent=2, sort_keys=True))
    if result["warnings"]:
        print(f"Completed with {len(result['warnings'])} warning(s).")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
