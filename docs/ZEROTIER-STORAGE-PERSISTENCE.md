# ZeroTier persistent storage integration

The integration uses Padavan's Storage MTD archive. Changes to ZeroTier identity, managed membership, local configuration, Moon files and custom planet are detected before daemon start; explicit membership synchronization also saves changes while the service is disabled. A failed save leaves a RAM retry marker and prevents service startup until the save succeeds. Periodic status and route refresh never invokes a flash save.

The base storage archive excludes only ZeroTier's regenerable peers.d cache and daemon PID/port files. Identity, networks.d files including per-network local.conf, Moon files, custom planet and unrelated user files remain included. All storage operations share a bounded lock; restarted rstats closes the lock descriptor.

The archive hash is staged separately and becomes current only after mtd_write reports success. Failed compression, capacity validation or flash writes do not promote the hash. An unchanged archive still skips a flash write.

## Evidence

Clean pinned-source preparation and shell syntax checks passed locally. An actual find selection fixture retained ten persistent files, including a filename containing a space, and excluded three runtime paths. Mock flash tests exercised failure, successful retry and unchanged archive write avoidance. Mock event tests exercised no-change, failed-save pending state and successful retry without a new state change. These tests did not execute physical MTD writes.

The expanded CI image verifier checks exact storage/lifecycle assets, syntax, cache-exclusion and transaction-lock markers, the change-save handler, and the BusyBox flock applet. Target compilation and final image verification are pending the new build.

Runtime acceptance remains outstanding: controlled save, real storage capacity, concurrent operations, fault/retry handling, and identity/membership restoration after a controlled reboot or upgrade. The project is not verified complete. No remote flash or reboot has been performed or authorized.
