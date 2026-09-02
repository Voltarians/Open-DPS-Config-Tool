import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]

class Gds2CaptureAssetsTests(unittest.TestCase):
    def test_program_and_launcher_exist(self):
        self.assertTrue((ROOT/'gds2_capture'/'Gds2Capture.ps1').is_file())
        self.assertTrue((ROOT/'gds2_capture'/'Start-GDS2-Capture.cmd').is_file())

    def test_passive_evidence_features(self):
        text=(ROOT/'gds2_capture'/'Gds2Capture.ps1').read_text(encoding='utf-8')
        for required in ('Get-FileHash','SHA256','Get-DiagnosticProcessSnapshot',
                         'Get-J2534RegistrationSnapshot','Get-WinEvent','events.jsonl'):
            self.assertIn(required,text)
        for forbidden in ('Invoke-WebRequest','Start-Process','LoadLibrary','WriteProcessMemory'):
            self.assertNotIn(forbidden,text)

    def test_no_vehicle_or_proprietary_payloads(self):
        names={p.name for p in (ROOT/'gds2_capture').rglob('*') if p.is_file()}
        self.assertNotIn('XMLFile.xml',names)
        self.assertFalse(any(name.lower().endswith(('.bin','.cal','.dll')) for name in names))

if __name__=='__main__':
    unittest.main()

