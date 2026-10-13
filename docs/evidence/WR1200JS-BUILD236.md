# WR1200JS test build 236

[Run 38428902691](https://github.com/Andrzej1973/padavan-4.4.198/actions/runs/38428902691) completed successfully. The manifest identifies `236_385d57d6` and reports image size 13,140,071 bytes with SHA256 `526de5315891306c23fbbb61321cc57dc870bf579039653f5fe400dc1b0803f4`. This is a workflow manifest hash, not an independently downloaded image hash.

Downloaded reports are preserved alongside this document:

- `build236-doh-image-checks.json`, artifact `11830133393`.
- `build236-stubby-image-checks.json`, artifact `11829998659`.

Both report `observed_process_ui`, `observed_process_backend` and shipped EN/UK/RU status labels as true. These gates cover presence of the manual button, visible-page refresh interval, role selector, linked handler marker and dictionary keys. They do not execute a browser on the router or prove resolver health.

The completed log `C:\Users\ANDRZEJ\Documents\Codex\2026-09-29\build236-log.txt` also records the handshake image gate passing at 16:22:28 UTC. This build includes joint interface/handshake refresh and DNS process refresh, but predates periodic ZRAM refresh and source-transfer retry handling.

No physical flashing, reboot or runtime verification was performed for this build. Device stability and full port completion remain unproven.
