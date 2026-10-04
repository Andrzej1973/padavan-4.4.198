# Band Steering transport requirements

Source inspected: vipshmily/padavan-4.4 at c25283e915a2a00a763774dd255b14aff997285e. Paths below are relative to trunk/linux-4.4.x/drivers/net/wireless/mediatek.

## Proven source and compiler findings

- Both drivers expose OID_BNDSTRG_MSG 0x0950. ap/ap_cfg.c dispatches to BndStrg_MsgHandle under BAND_STEERING; mt76x3 additionally passes the selected BSS index.
- ap/ap_band_steering.c sends binary messages through RtmpOSWrielessEventSend. os/linux/rt_linux.c sets iwreq_data flags and length and calls wireless_send_event. The adapter must select the source interface before decoding an event; the OID alone does not identify the protocol.
- The target GCC 10.5.0 probe run 37177074123 established mt76x2 message size 32/alignment 4 and mt76x3 size 80/alignment 8. Source hashes and actual downloaded MIPS objects were independently verified locally. This proves the extracted declarations under the probe compiler flags, not yet a complete driver build with Band Steering enabled.
- mt76x2 handler requires exactly sizeof(BNDSTRG_MSG). mt76x3 rejects only lengths greater than sizeof(BNDSTRG_MSG) and zero-initializes its local message. Earlier notes claiming both required exact size were inaccurate. The adapter should always send the complete correct structure and strictly validate received event lengths.
- mt76x3 on/off handling stores current->pid as DaemonPid. Subsequent commands from another PID emit REJECT_EVENT. One persistent process must own enable, client commands, heartbeat and orderly disable; a series of separate CLI processes is insufficient.
- mt76x3 HEARTBEAT_MONITOR increments a counter. BndStrgHeartBeatMonitor releases steering after 20 unchanged monitor observations. The actual invocation frequency still needs tracing; do not assume 20 seconds.
- mt76x3 first enable calls BndStrg_KickOutAllSta for participating BSSs and deletes corresponding client table entries. The WebUI must explain this reconnect behavior. Factory runtime enable remains off.
- CLI_DEL semantics differ: mt76x3 can actively deauthenticate an associated client; the legacy command deletes its steering table entry. These operations cannot be treated as interchangeable by the policy.

## Required next work

Complete private ioctl routing and flags, wireless-event framing, interface/BSS mapping, heartbeat scheduling, exact nested field offsets, driver compile flags and packing audit. Then implement per-radio encoding/decoding, bounded client tracking and policy with lifecycle recovery. Full image compilation and real router/client behavior remain required. No Band Steering enablement or live router changes have been performed.
