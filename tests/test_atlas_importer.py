import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from atlas_importer.session_importer import import_bundle


class AtlasImporterTests(unittest.TestCase):
    def make_bundle(self, root: Path, schema: str = "opendps.gds2-capture.v1") -> Path:
        bundle = root / "bundle"
        evidence = bundle / "evidence" / "_versions" / "C" / "GM" / "trace_00A1.log"
        evidence.mkdir(parents=True)
        payload = evidence / "20260902-trace_00A1.log"
        payload.write_text("synthetic diagnostic trace\n", encoding="utf-8")
        digest = hashlib.sha256(payload.read_bytes()).hexdigest()
        manifest = {
            "schema": schema,
            "session": "TEST-SESSION",
            "started_utc": "2026-09-02T12:00:00Z",
            "stopped_utc": "2026-09-02T12:01:00Z",
            "computer": "PRIVATE-PC",
            "user": "PrivateUser",
            "files": [
                {
                    "source_path": r"C:\Users\PrivateUser\GM\trace_00A1.log",
                    "evidence_path": r"_versions/C/GM/trace_00A1.log/20260902-trace_00A1.log",
                    "size_bytes": payload.stat().st_size,
                    "sha256": digest,
                    "captured_utc": "2026-09-02T12:00:30Z",
                    "reason": "created",
                },
                {
                    "source_path": r"C:\Users\PrivateUser\GM\duplicate.log",
                    "evidence_path": r"_versions/C/GM/trace_00A1.log/20260902-trace_00A1.log",
                    "size_bytes": payload.stat().st_size,
                    "sha256": digest,
                    "captured_utc": "2026-09-02T12:00:31Z",
                    "reason": "modified",
                },
            ],
        }
        (bundle / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        return bundle

    def test_import_redacts_and_deduplicates(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bundle = self.make_bundle(root)
            result = import_bundle(bundle, root / "output", vehicle_id="volt-test")
            self.assertEqual(result["session"]["source"], "gds2")
            self.assertEqual(result["session"]["vehicle_id"], "volt-test")
            self.assertEqual(len(result["artifacts"]), 1)
            self.assertEqual(result["artifacts"][0]["observations"], 2)
            exported = (root / "output" / "atlas-session.json").read_text()
            self.assertNotIn("PRIVATE-PC", exported)
            self.assertNotIn("PrivateUser", exported)
            self.assertEqual(result["artifacts"][0]["hash_status"], "verified")

    def test_sps_schema_and_zip_input(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bundle = self.make_bundle(root, "opendps.sps-capture.v1")
            archive = root / "capture.zip"
            with zipfile.ZipFile(archive, "w") as output:
                for path in bundle.rglob("*"):
                    if path.is_file():
                        output.write(path, Path("capture") / path.relative_to(bundle))
            result = import_bundle(archive, root / "output")
            self.assertEqual(result["session"]["source"], "sps2")

    def test_rejects_unknown_schema(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bundle = self.make_bundle(root, "unknown")
            with self.assertRaisesRegex(ValueError, "Unsupported"):
                import_bundle(bundle, root / "output")


if __name__ == "__main__":
    unittest.main()

