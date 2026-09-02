# SPS2 capture subsystem

The utility in `sps_capture/` is separate from `opendps_config`. Capture
preserves what SPS2 placed on disk; archive analysis or transformation works on
a copy.

## Processing boundary

1. Inventory selected cache and log roots.
2. Poll for created or modified files.
3. Wait for each candidate to become stable.
4. Preserve every observed version under its original drive-relative location.
5. Calculate SHA-256 and append an event.
6. Perform a final scan after Ctrl+C.
7. Write and hash the session manifest.

Before a paid SPS session, validate this against a temporary tree by creating,
modifying, renaming, and deleting test files. Confirm evidence bytes and hashes,
manually verify all SPS cache roots, and ensure adequate destination space.
