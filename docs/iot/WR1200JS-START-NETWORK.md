# Experimental pre-OPEN network owner

`start-network.c` consumes retained staged startup admission under the existing
shutdown/service owner. It checks exact staged values and expected gates plus
current initial-idle epoch/generation/increasing serial before every phase.

Sequence: bridge prepare, quarantine, attach ra2, bridge UP, network gate1,
DNS prepare, policy enable and read-only readiness. Firewall remains0 until
policy and ra2 remains DOWN throughout. This object issues no OPEN and does
not commit DNS or release startup snapshot.

Any potentially partial mutation failure moves to RECOVERY and refuses replay.
A separate rollback owner must quiesce the correct driver context and recover
bridge/services/baseline. Never reset this object to repeat an ambiguous write.

Host checks execute actual sequencer and request matcher/gate writer with
external kernel/NVRAM/DNS adapters injected. Target/source verification and
physical acceptance remain separate. Production dispatch is unbound.
