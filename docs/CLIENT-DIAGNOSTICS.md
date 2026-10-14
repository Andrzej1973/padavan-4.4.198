# WR1200JS one-shot client collection diagnostics

These diagnostics isolate the unavailable client-list source without replacing firmware or restarting services. They are not a repair or proof of complete router acceptance.

The `Band Steering driver ABI` workflow builds static MIPS32r2/o32 soft-float binaries using the pinned toolchain. The `wr1200js-client-diagnostics` artifact contains both binaries and `client-diagnostics.sha256`. Check the run's exact commit, successful diagnostic compilation/native fixture step, and SHA256 values before copying a binary to the device. Artifact presence alone does not establish that every later workflow step passed.

## Device operation

Use an authorized SSH session on WR1200JS. Copy the verified binaries to a unique directory in `/tmp`, give only the owner execute permission, and run each once with no arguments. They have a three-second alarm and do not change NVRAM, service configuration, radio settings or flash contents. Do not install them as services or schedule repeated execution.

- `wr-networkmap-diagnostic` uses the production source collector on `/tmp/static_ip.inf` and `/var/lock/networkmap.lock`. It briefly obtains a nonblocking POSIX lock, reads and validates the snapshot, and prints only record/invalid/truncated counts. A missing/non-regular lock fails preflight. The shared production collector opens the lock with `O_CREAT`; a concurrent removal after preflight could therefore recreate that temporary lock file. It never writes lock metadata.
- `wr-radio-diagnostic` opens a datagram socket and sends only `RTPRIV_IOCTL_GET_MAC_TABLE_STRUCT` to fixed `ra0` and `rai0`. It uses the actual checked shared-header layout and the production wire decoder. The decoder uses two receive streams, matching the live WR1200JS settings observed during this investigation. It prints the ioctl return code, errno, returned length and decoded count for each radio. It does not print MAC addresses, IP addresses or names.

Exit 0 means that diagnostic collected/decoded its source, exit 1 means unavailable/invalid, exit 2 means unexpected arguments. An alarm termination is a diagnostic timeout, not a successful result. A networkmap success does not prove station-table success; a radio success does not prove that httpd has the same code, credentials or source timing. Retain these distinctions when interpreting results from an older installed image.

## Verification scope

Native fixtures cover networkmap success, missing-lock failure and unchanged lock metadata. Existing collector tests cover nonblocking contention, source symlink/FIFO rejection and stale cache behavior. Wrapped native radio tests cover fixed read-only queries, successful empty tables, short replies and ioctl errors. MIPS compilation checks the actual header ABI. Physical execution and comparison with the installed HTTP handler remain required; none of these tests prove WAN/LAN forwarding, long-term stability or configuration retention.
