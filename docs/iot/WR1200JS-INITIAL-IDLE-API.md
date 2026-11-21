# Experimental initial-idle configuration API

Query17/reply18 on the existing privileged64-byte observation transport checks
only the never-opened ra2 registration. Previous OPEN/CLOSE history is refused;
such attempts must use their own refusal or CLOSE recovery path.

Persistent adapter storage is initialized once with the existing API owners.
RTNL and caller lifetime ownership span a BSS_OBSERVE ticket and the existing
beacon/TBTT/producer-generation/DMA/TxS configuration observer. Ring and
transition locks remain disjoint. Final admission rechecks controls and exact
registration. Retirement of a failed readback does not count as acceptance.
A separate accepted marker and exact current/retired serial are required before
reply encoding. User copy occurs outside transition lock.

An active persistent probe blocks both public recovery-idle and exclusive
reaper-join final retirement. A foreign ticket retains context and poisons
admission; the normal reaper still returns only its own completed reference.
No descriptor freeing, firmware ACK policy or radio timing is changed.

Only the separate no-host experiment installs this24-path source bundle.
It is configuration observation, not loaded-key acceptance, RF silence or a
lease authorizing later OPEN. RC integration, target module compilation and
physical WR1200JS testing remain separate requirements.
