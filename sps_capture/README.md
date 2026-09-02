# SPS2 Capture

SPS2 Capture is a separate, passive Windows program for preserving files that
appear or change while SPS2/Techline Connect downloads calibration material.
It does not intercept encrypted network traffic, inject into processes, modify
SPS2, or write to a vehicle.

## Quick start

1. Close SPS2 and Techline Connect.
2. Discover recognized directories:

   ```powershell
   .\SpsCapture.ps1 -Command Discover
   ```

3. Start capture, explicitly adding every known cache or log path:

   ```powershell
   .\SpsCapture.ps1 -WatchPath 'C:\ProgramData\GM','C:\Users\Monroe\AppData\Local\GM'
   ```

4. Run SPS2 normally and let its workflow finish.
5. Return to the capture window and press **Ctrl+C**.
6. Wait for the final collection window.

The double-clickable `Start-SPS-Capture.cmd` accepts the same arguments. Output
defaults to `SPS-Captures` on the Windows Desktop.

## Evidence bundle

- `baseline.json`: metadata present before SPS2 started
- `events.jsonl`: append-only capture events and copy errors
- `evidence/_versions/`: immutable copies with drive-relative layout preserved
- `inventory.csv`: human-readable captured-file inventory
- `manifest.json`: session information and SHA-256 hashes
- `manifest.sha256`: hash of the completed manifest

Storage locations vary by SPS/Techline revision. Discovery is not a guarantee;
verify the actual cache and log directories and pass them with `-WatchPath`.

The archive creator must consume a **copy** of a completed bundle. The evidence
record stays unchanged. DPS Type 4 conversion remains a separate validation-gated
operation.
