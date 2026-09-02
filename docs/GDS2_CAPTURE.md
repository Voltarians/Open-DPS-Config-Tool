# GDS2 capture subsystem

The `gds2_capture/` program preserves diagnostic-session artifacts separately
from SPS programming downloads and OpenDPS archive work.

## Collection layers

1. Filesystem baseline and changed-file versions.
2. GDS2, Techline, VCX, J2534, and related process snapshots.
3. Installed SAE J2534 pass-through registration metadata.
4. Relevant Windows Application event-log entries.
5. Optional files written by an independent CAN capture utility.

The optional CAN logger must use its own supported hardware and output files.
GDS2 Capture does not place another process between GDS2 and the vehicle.

## Validation gate

Before vehicle use, run the utility against a temporary directory on the target
Windows computer. Create and modify representative files, verify every SHA-256
hash, check the process and registry snapshots, and establish the actual GDS2
and interface-driver data paths.

