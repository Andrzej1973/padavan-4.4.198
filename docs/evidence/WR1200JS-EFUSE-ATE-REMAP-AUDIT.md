# EFUSE / ATE / reset source paths — 2026-11-06

Inspected the preserved isolated driver and current admission generators.
These are source paths, not proof of every effective config/runtime caller.

| Path | Identified entry / ownership | Remaining limit |
| --- | --- | --- |
| eFuse_init | chipOps.eeinit callback installed by EEPROM hook; called by EEPROM init and MULTIPLE_CARD profile setup | Alternate hooks and effective guards need confirmation |
| rtmp_ee_load_from_efuse | eFuse_init and CONFIG_ATE load-buffer control | Distinguish synchronous init from external control |
| EEPROM BIN / EFUSE / writeback controls | ap/ap_cfg.c command table; Linux ioctl holds control reference | Other internal calls require scope review |
| QA writeback | qa_agent.c callbacks, RtmpDoAte → HQA_CMDHandler | Sole identified RtmpDoAte call is CMD_RTPRIV_IOCTL_ATE in RTMP_COM_IoctlHandle, under CONFIG_ATE/CONFIG_QA |
| NICResetFromError | Definition/prototype, invokes NICInitializeAdapter and EEPROM restore | No caller found; this is not binary proof |
| PSE / PDMA reset | wr_iot_radio_reset_drain owns RTNL, peer executor and transition before raw callbacks | VOID return is not hardware success |
| MCU events | Generic rx_event_handler runs only with boot_active false; checked ACK parser remains available | Prior RX execution must be joined by ROM quiesce |

Main open calls MCUSysInit before EEPROM hook and NICInitializeAdapter. These
specific synchronous init writes follow the proposed scheduler placement on
the same owner. The current gate still refuses bootstrap success immediately
after MCUSysInit; production activation remains unimplemented. This ordering
does not serialize two ordinary remap users with each other.

The assembled candidate already blocks generic RX-event fallback using
boot_active. The earlier RX-direct generator alone does not show this later
nettask/open-layer protection. Existing RX-bounds checks cover blocked generic
dispatch; no duplicate fence was added.

Before binding, finish effective-config/all-producer coverage and normal-startup
command policy: denied transition commands currently discard instead of replay.
Then verify firmware receipt, checked scheduler and normal sender/data promotion
as a connected path, with retained failure. Router runtime remains unverified.
