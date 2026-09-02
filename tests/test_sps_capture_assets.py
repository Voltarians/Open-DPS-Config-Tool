import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class SpsCaptureAssetsTests(unittest.TestCase):
    def test_program_and_launcher_exist(self):
        self.assertTrue((ROOT / 'sps_capture' / 'SpsCapture.ps1').is_file())
        self.assertTrue((ROOT / 'sps_capture' / 'Start-SPS-Capture.cmd').is_file())

    def test_capture_is_passive_and_hashes_evidence(self):
        script=(ROOT / 'sps_capture' / 'SpsCapture.ps1').read_text(encoding='utf-8')
        for required in ('Get-FileHash','SHA256','baseline.json','events.jsonl'):
            self.assertIn(required,script)
        self.assertNotIn('Invoke-WebRequest',script)
        self.assertNotIn('Start-Process',script)

    def test_no_proprietary_xml_asset(self):
        names={p.name for p in (ROOT / 'sps_capture').rglob('*') if p.is_file()}
        self.assertNotIn('XMLFile.xml',names)

if __name__ == '__main__':
    unittest.main()

