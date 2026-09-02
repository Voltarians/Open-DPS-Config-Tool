# GDS2 Capture

GDS2 Capture is a separate passive Windows program for preserving diagnostic
session evidence produced by GDS2, Techline components, VCX software, J2534
drivers, and an optional independent CAN logger.

It does not hook or inject into GDS2, proxy J2534 calls, decrypt traffic, send
diagnostic requests, or communicate with the vehicle.

## Quick start

1. Close GDS2 and related diagnostic applications.
2. Discover common diagnostic directories:

   ```powershell
   .\Gds2Capture.ps1 -Command Discover
   ```

3. Start capture with every verified log/cache location. If a CAN tool is
   logging to disk, include its output directory separately:

   ```powershell
   .\Gds2Capture.ps1 `
     -WatchPath 'C:\ProgramData\GM','C:\Users\Monroe\AppData\Local\GM' `
     -CanCapturePath 'D:\CAN-Captures'
   ```

4. Start GDS2 and perform the diagnostic session normally.
5. Export reports and logs before closing GDS2.
6. Return to the capture window and press **Ctrl+C**.
7. Wait for the final collection window.

`Start-GDS2-Capture.cmd` provides a double-clickable launcher and accepts the
same arguments. Output defaults to `GDS2-Captures` on the Desktop.

## Evidence bundle

- `baseline.json`: pre-session file inventory
- `processes-start.json` and `processes-stop.json`: relevant process snapshots
- `j2534-registration.json`: registered 32-bit and 64-bit pass-through drivers
- `windows-application-events.json`: relevant Application log events
- `events.jsonl`: append-only file-capture events and errors
- `evidence/_versions/`: immutable copies of each observed file version
- `inventory.csv`: captured-file index
- `manifest.json` and `manifest.sha256`: machine-readable manifest and hash

## Limitations

Filesystem capture cannot prove every request and response exchanged through a
J2534 device. That requires vendor-supported debug logging or a separately
validated pass-through logger. This first version deliberately avoids an
injected J2534 shim because it could destabilize a live diagnostic session.

Directory locations vary by GDS2, Techline, and interface-driver revision.
Automatic discovery is only a starting point. Verify actual paths before the
session; evidence from an unwatched temporary directory cannot be recovered.

