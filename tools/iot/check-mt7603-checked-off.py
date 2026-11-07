#!/usr/bin/env python3
"""Run fault injection against the exact checked-off C body generated for v40."""

import importlib.util
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[2]
GENERATOR = Path(__file__).with_name("prepare-mt7603-checked-off-candidate.py")
OUTPUT = ROOT / ".iot-local-check" / "mt7603-checked-off-host.exe"

spec = importlib.util.spec_from_file_location("mt7603_checked_off", GENERATOR)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

PREFIX = r'''
#include <stdio.h>
#include <stdlib.h>
typedef unsigned int UINT32;
typedef unsigned long ULONG;
typedef int INT32;
typedef int BOOLEAN;
#define TRUE 1
#define FALSE 0
#define HIF_MT 1
#define WR_RADIO_CLOSE 2
#define ASIC_MAC_RX 2
#define ASIC_MAC_TXRX 3
#define PDMA_TX_RX 4
#define WIFI_RADIO_OFF 5
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE -1
#define NDIS_STATUS_RESOURCES -2
#define ARB_SCR 0x10
#define ARB_TQCR0 0x11
#define ARB_RQCR 0x12
#define MT_WPDMA_GLO_CFG 0x20
#define ARB_RQCR_RX_START 1U
#define MT_ARB_SCR_RXDIS (1U << 9)
#define MT_ARB_SCR_TXDIS (1U << 8)
#define TX_DMA_BUSY 4U
#define RX_DMA_BUSY 8U
#define fRTMP_ADAPTER_NIC_NOT_EXIST 1U
#define fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET 2U
#define fRTMP_ADAPTER_RADIO_OFF 4U
#define fRTMP_ADAPTER_INTERRUPT_ACTIVE 8U
typedef union {
 UINT32 word;
 struct { UINT32 EnableTxDMA:1; UINT32 EnableRxDMA:1; UINT32 rest:30; } field;
} WPDMA_GLO_CFG_STRUC;
struct wr_iot_radio_ticket { int operation; unsigned int serial; };
struct transition { int busy; unsigned int serial; unsigned int mt_radio_off_stage; };
typedef struct adapter {
 void *net_dev;
 struct { int hif_type; } chipCap;
 int mt7603, iwpriv_command, wr_iot_transition_lock;
 unsigned int flags, arb, rqcr, tqcr0, dma;
 struct transition wr_iot_transition;
 int queue_calls, mac_calls, poll_calls, cmd_calls, pdma_calls, irq_calls;
 int fail_mac, fail_mac_write_silent, fail_poll, fail_cmd, fail_pdma;
 int fail_arb_read, fail_rqcr_read, fail_tqcr0_read, fail_dma_read;
 int drop_rx_rqcr_write, drop_tx_rqcr_write, drop_tx_tqcr0_write;
} RTMP_ADAPTER;
#define IS_MT7603(p) ((p)->mt7603)
#define RTMP_TEST_FLAG(p,f) (((p)->flags & (f)) != 0)
#define RTMP_SET_FLAG(p,f) ((p)->flags |= (f))
#define RTMP_IRQ_LOCK(lock, flags) ((void)(lock), (void)(flags))
#define RTMP_IRQ_UNLOCK(lock, flags) ((void)(lock), (void)(flags))
#define RTMP_OS_NETDEV_STOP_QUEUE(dev) (active->queue_calls++)
#define RTMP_ASIC_INTERRUPT_DISABLE(p) ((p)->irq_calls++)
#define RTMP_IO_READ32(p, reg, dst) do { \
 *(dst) = (reg) == ARB_SCR ? ((p)->fail_arb_read ? 0xffffffffU : (p)->arb) : \
   (reg) == ARB_RQCR ? ((p)->fail_rqcr_read ? 0xffffffffU : (p)->rqcr) : \
   (reg) == ARB_TQCR0 ? ((p)->fail_tqcr0_read ? 0xffffffffU : (p)->tqcr0) : \
   ((p)->fail_dma_read ? 0xffffffffU : (p)->dma); \
} while (0)
static RTMP_ADAPTER *active;
static INT32 AsicSetMacTxRx(RTMP_ADAPTER *p, int path, BOOLEAN enable) {
 (void)enable; p->mac_calls++;
 if (p->fail_mac) return FALSE;
 if (p->fail_mac_write_silent) return TRUE;
 p->arb |= path == ASIC_MAC_TXRX ?
     MT_ARB_SCR_TXDIS | MT_ARB_SCR_RXDIS : MT_ARB_SCR_RXDIS;
 if (path == ASIC_MAC_TXRX) {
  if (!p->drop_tx_tqcr0_write) p->tqcr0 = 0;
  if (!p->drop_tx_rqcr_write) p->rqcr &= ~ARB_RQCR_RX_START;
 } else if (!p->drop_rx_rqcr_write) {
  p->rqcr &= ~ARB_RQCR_RX_START;
 }
 return TRUE;
}
static BOOLEAN wr_iot_mt_poll_txrx_empty(RTMP_ADAPTER *p) {
 p->poll_calls++; return !p->fail_poll;
}
static INT32 wr_iot_send_radio_off_checked(RTMP_ADAPTER *p) {
 p->cmd_calls++; return p->fail_cmd ? NDIS_STATUS_FAILURE : NDIS_STATUS_SUCCESS;
}
static INT32 AsicSetWPDMA(RTMP_ADAPTER *p, int path, BOOLEAN enable) {
 (void)path; (void)enable; p->pdma_calls++;
 if (p->fail_pdma) return FALSE;
 p->dma = 0; return TRUE;
}
'''

SUFFIX = r'''
static void require(int condition, const char *message) {
 if (!condition) { fprintf(stderr, "FAIL: %s\n", message); exit(1); }
}
static RTMP_ADAPTER fresh(void) {
 RTMP_ADAPTER p = {0};
 p.net_dev = (void *)1; p.chipCap.hif_type = HIF_MT; p.mt7603 = 1;
 p.wr_iot_transition.busy = WR_RADIO_CLOSE;
 p.wr_iot_transition.serial = 42;
 p.flags = fRTMP_ADAPTER_INTERRUPT_ACTIVE;
 p.rqcr = ARB_RQCR_RX_START; p.tqcr0 = 0x55U;
 p.dma = 3;
 return p;
}
int main(void) {
#ifdef LOAD_FW_ONE_TIME
 struct wr_iot_radio_ticket ticket = {WR_RADIO_CLOSE, 42};
 RTMP_ADAPTER p = fresh(); active = &p;
 require(!wr_iot_mt_radio_off_checked(&p, &ticket),
         "LOAD_FW_ONE_TIME must retain fail-closed refusal");
 require(!p.queue_calls && !p.mac_calls && !p.cmd_calls && !p.pdma_calls,
         "LOAD_FW_ONE_TIME refusal mutated device state");
 puts("PASS LOAD_FW_ONE_TIME checked close remains fail-closed before mutation");
 return 0;
#else
 struct wr_iot_radio_ticket ticket = {WR_RADIO_CLOSE, 42};
 struct wr_iot_radio_ticket wrong = {WR_RADIO_CLOSE, 41};
 RTMP_ADAPTER p = fresh(); active = &p;
 require(!wr_iot_mt_radio_off_checked(&p, &wrong), "wrong ticket accepted");
 require(p.cmd_calls == 0, "wrong ticket issued MCU command");
 p = fresh(); active = &p; p.chipCap.hif_type = 0;
 require(!wr_iot_mt_radio_off_checked(&p, &ticket), "unsupported HIF accepted");
 require(!p.queue_calls && !p.mac_calls && !p.cmd_calls,
         "unsupported HIF mutated close state");
 p = fresh(); active = &p;
 require(wr_iot_mt_radio_off_checked(&p, &ticket), "normal close failed");
 require(p.wr_iot_transition.mt_radio_off_stage == 4 && p.cmd_calls == 1 &&
         p.pdma_calls == 1 && p.mac_calls == 2 &&
         p.queue_calls == 1 && p.irq_calls == 1,
         "normal close milestone/call count");

 p = fresh(); active = &p; p.fail_mac_write_silent = 1;
 require(!wr_iot_mt_radio_off_checked(&p, &ticket),
         "silent MAC write failure accepted");
 require(p.wr_iot_transition.mt_radio_off_stage == 0 && p.cmd_calls == 0,
         "silent RX write failure advanced to MCU");
 p.fail_mac_write_silent = 0;
 require(wr_iot_mt_radio_off_checked(&p, &ticket),
         "MAC write retry failed");

 p = fresh(); active = &p; p.drop_rx_rqcr_write = 1;
 require(!wr_iot_mt_radio_off_checked(&p, &ticket),
         "RX request left enabled after MAC RX stop");
 require(p.cmd_calls == 0 && p.wr_iot_transition.mt_radio_off_stage == 0,
         "RX request readback failure advanced to MCU");

 p = fresh(); active = &p; p.fail_rqcr_read = 1;
 require(!wr_iot_mt_radio_off_checked(&p, &ticket),
         "invalid RX request register readback accepted");
 require(p.cmd_calls == 0 && p.wr_iot_transition.mt_radio_off_stage == 0,
         "invalid RX request readback advanced to MCU");

 p = fresh(); active = &p; p.wr_iot_transition.mt_radio_off_stage = 3;
 p.arb = MT_ARB_SCR_RXDIS; p.fail_mac_write_silent = 1;
 require(!wr_iot_mt_radio_off_checked(&p, &ticket),
         "silent TX disable failure accepted");
 require(p.pdma_calls == 0 && p.wr_iot_transition.mt_radio_off_stage == 3,
         "silent TX failure advanced to PDMA");
 p.fail_mac_write_silent = 0;
 require(wr_iot_mt_radio_off_checked(&p, &ticket),
         "TX disable retry failed");

 p = fresh(); active = &p; p.wr_iot_transition.mt_radio_off_stage = 3;
 p.arb = MT_ARB_SCR_RXDIS; p.rqcr = 0; p.tqcr0 = 0x55U;
 p.drop_tx_tqcr0_write = 1;
 require(!wr_iot_mt_radio_off_checked(&p, &ticket),
         "nonempty TX queue control accepted after MAC TX stop");
 require(p.pdma_calls == 0 && p.wr_iot_transition.mt_radio_off_stage == 3,
         "TX queue control failure advanced to PDMA");

 p = fresh(); active = &p; p.wr_iot_transition.mt_radio_off_stage = 3;
 p.arb = MT_ARB_SCR_RXDIS; p.rqcr = 0; p.tqcr0 = 0;
 p.fail_tqcr0_read = 1;
 require(!wr_iot_mt_radio_off_checked(&p, &ticket),
         "invalid TX queue control readback accepted");
 require(p.pdma_calls == 0 && p.wr_iot_transition.mt_radio_off_stage == 3,
         "invalid TX queue control readback advanced to PDMA");

 p = fresh(); active = &p; p.wr_iot_transition.mt_radio_off_stage = 3;
 p.arb = MT_ARB_SCR_RXDIS; p.rqcr = ARB_RQCR_RX_START; p.tqcr0 = 0;
 p.drop_tx_rqcr_write = 1;
 require(!wr_iot_mt_radio_off_checked(&p, &ticket),
         "RX request re-enabled before DMA stop");
 require(p.pdma_calls == 0 && p.wr_iot_transition.mt_radio_off_stage == 3,
         "RX request failure advanced to PDMA");

 p = fresh(); active = &p; p.wr_iot_transition.mt_radio_off_stage = 3;
 p.arb = MT_ARB_SCR_RXDIS; p.fail_arb_read = 1;
 require(!wr_iot_mt_radio_off_checked(&p, &ticket),
         "invalid TX/RX MAC readback accepted");
 require(p.pdma_calls == 0 && p.wr_iot_transition.mt_radio_off_stage == 3,
         "invalid TX/RX readback advanced to PDMA");

 p = fresh(); active = &p; p.fail_poll = 1;
 require(!wr_iot_mt_radio_off_checked(&p, &ticket), "poll failure accepted");
 require(p.wr_iot_transition.mt_radio_off_stage == 1 && p.cmd_calls == 0,
         "poll failure advanced to MCU");
 p.fail_poll = 0;
 require(wr_iot_mt_radio_off_checked(&p, &ticket), "poll retry failed");
 require(p.queue_calls == 1 && p.cmd_calls == 1,
         "poll retry restarted queue or duplicated MCU command");

 p = fresh(); active = &p; p.fail_cmd = 1;
 require(!wr_iot_mt_radio_off_checked(&p, &ticket), "MCU failure accepted");
 require(p.wr_iot_transition.mt_radio_off_stage == 5 && p.cmd_calls == 1,
         "uncertain MCU outcome not retained");
 p.fail_cmd = 0;
 require(!wr_iot_mt_radio_off_checked(&p, &ticket), "uncertain MCU retry accepted");
 require(p.cmd_calls == 1 && p.pdma_calls == 0, "MCU command replayed");

 p = fresh(); active = &p; p.fail_pdma = 1;
 require(!wr_iot_mt_radio_off_checked(&p, &ticket), "PDMA failure accepted");
 require(p.wr_iot_transition.mt_radio_off_stage == 3 && p.cmd_calls == 1,
         "PDMA failure lost MCU progress");
 p.fail_pdma = 0;
 require(wr_iot_mt_radio_off_checked(&p, &ticket), "PDMA retry failed");
 require(p.cmd_calls == 1 && p.pdma_calls == 2, "PDMA retry replayed MCU");

 p = fresh(); active = &p; p.fail_arb_read = 1;
 require(!wr_iot_mt_radio_off_checked(&p, &ticket), "invalid ARB read accepted");
 require(p.cmd_calls == 0, "invalid ARB read advanced to MCU");
 p = fresh(); active = &p; p.fail_dma_read = 1;
 require(!wr_iot_mt_radio_off_checked(&p, &ticket), "invalid PDMA read accepted");
 require(p.wr_iot_transition.mt_radio_off_stage == 3 && p.cmd_calls == 1,
         "invalid PDMA read lost command result");
 p.fail_dma_read = 0;
 require(wr_iot_mt_radio_off_checked(&p, &ticket), "PDMA readback retry failed");
 require(p.cmd_calls == 1, "PDMA readback retry replayed MCU");

 puts("PASS checked MT7603 stop: MAC readback, ordered milestones, fault retention, no MCU replay");
 return 0;
#endif
}
'''


def main() -> None:
    source = PREFIX + module.CHECKED_OFF + SUFFIX
    with tempfile.TemporaryDirectory(prefix="wr-iot-checked-off-") as directory:
        normal = Path(directory) / "normal"
        load_once = Path(directory) / "load-once"
        for output, flags in ((normal, []), (load_once, ["-DLOAD_FW_ONE_TIME=1"])):
            subprocess.run(
                ["gcc", "-std=c11", "-Wall", "-Wextra", "-Werror", *flags,
                 "-x", "c", "-", "-o", str(output)],
                input=source, text=True, check=True,
            )
            subprocess.run([str(output)], check=True)


if __name__ == "__main__":
    main()
