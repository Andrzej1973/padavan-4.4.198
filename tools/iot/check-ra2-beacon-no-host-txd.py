#!/usr/bin/env python3
"""Compile the unbound decoder with actual vendor little-endian bitfields."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('header', type=Path, help='vendor include/mac/mac_mt/mt_mac.h')
a = p.parse_args()
s = a.header.read_text()
parts = []
for i in range(8):
    records = re.findall(r'typedef struct GNU_PACKED tmac_txd_' + str(i) +
                         r' \{.*?\} TMAC_TXD_' + str(i) + r';', s, re.S)
    if i == 4 and len(records) == 1 and re.search(r'UINT32\s+pn_low\s*;', records[0]):
        parts.append(records[0])  # Entire DWORD, no endian bitfield alternative.
        continue
    if len(records) != 2:
        raise SystemExit('Expected reviewed big/little-endian TXD pair: ' + str(i))
    parts.append(records[1])
start = s.index('typedef struct GNU_PACKED _TMAC_TXD_L {')
parts.append(s[start:s.index('} TMAC_TXD_L;', start) + len('} TMAC_TXD_L;')])
for name in ('P_IDX_LMAC', 'Q_IDX_BCN', 'TMI_FT_LONG', 'TMI_HDR_FT_NOR_80211'):
    value = re.findall(r'^#define\s+' + name + r'\s+(0x[0-9a-fA-F]+|[0-9]+)\s*$', s, re.M)
    if len(value) != 1:
        raise SystemExit('Changed vendor constant: ' + name)
    parts.append('#define ' + name + ' ' + value[0])
prefix = '''#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef uint32_t UINT32;
#define MT7603 1
#define GNU_PACKED __attribute__((packed))
#define NdisMoveMemory memcpy
#define FC_TYPE_MGMT 0
#define SUBTYPE_BEACON 8
'''
tail = r'''
#include "ra2-beacon-no-host-txd.h"
#include "beacon-producer-gate.h"
typedef struct packet {void *data;unsigned len;} *PNDIS_PACKET;
struct device {int running;};
typedef struct {
 int chip;
 struct {unsigned BssidNum;struct {
  struct {struct device *if_dev;} wdev;
  struct {PNDIS_PACKET BeaconPkt;int bBcnSntReq,bcn_state;} bcn_buf;
 } MBSSID[3];} ApCfg;
 struct wr_iot_beacon_producer_gate wr_iot_beacon_gates[3];
} RTMP_ADAPTER;
#define IS_MT7603(ad) ((ad)->chip==0x7603)
#define netif_running(dev) ((dev)->running)
#define BCN_TX_IDLE 0
#define GET_OS_PKT_LEN(pkt) ((pkt)->len)
#define GET_OS_PKT_DATAPTR(pkt) ((pkt)->data)
#include "ra2-beacon-no-host-packet.h"
static void packet_scope(void){
 for(unsigned fault=0;fault<11;fault++){
  TMAC_TXD_L d={0};d.txd_0.q_idx=Q_IDX_BCN;
  d.txd_1.ft=TMI_FT_LONG;d.txd_1.own_mac=0x12;d.txd_1.no_ack=1;
  d.txd_1.hdr_format=TMI_HDR_FT_NOR_80211;
  d.txd_2.sub_type=SUBTYPE_BEACON;d.txd_2.bc_mc_pkt=1;
  struct packet packet={&d,sizeof(d)};PNDIS_PACKET input=&packet;
  struct device dev={1};RTMP_ADAPTER ad={.chip=0x7603,.ApCfg.BssidNum=3};
  struct wr_iot_beacon_producer_ticket ticket={0};const void *bytes=&d;
  unsigned length=sizeof(d);int dma=0;
  ad.ApCfg.MBSSID[2].wdev.if_dev=&dev;
  ad.ApCfg.MBSSID[2].bcn_buf.BeaconPkt=&packet;
  ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=1;
  assert(wr_iot_beacon_gate_open(&ad.wr_iot_beacon_gates[2],1));
  assert(wr_iot_beacon_gate_begin(&ad.wr_iot_beacon_gates[2],1,&ticket));
  switch(fault){
  case 1:input=(PNDIS_PACKET)(uintptr_t)1;break; /* Must not dereference foreign skb. */
  case 2:ticket.generation++;break;
  case 3:ad.wr_iot_beacon_gates[2].active=2;break;
  case 4:length--;break;
  case 5:bytes=(const void *)(uintptr_t)1;break;
  case 6:ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=0;break;
  case 7:dma=1;break;
  case 8:dma=-1;break;
  case 9:ad.ApCfg.MBSSID[2].bcn_buf.bcn_state=2;break;
  case 10:assert(wr_iot_beacon_gate_revoke(&ad.wr_iot_beacon_gates[2],1));break;
  }
  RTMP_ADAPTER before=ad;TMAC_TXD_L descriptor_before=d;
  assert(wr_iot_ra2_no_host_packet(&ad,input,&ticket,bytes,length,dma)==(fault==0));
  assert(!memcmp(&before,&ad,sizeof(ad))&&!memcmp(&descriptor_before,&d,sizeof(d)));
 }
}
int main(void){
 packet_scope();
 for(unsigned fault=0;fault<14;fault++){
  TMAC_TXD_L d={0};d.txd_0.q_idx=Q_IDX_BCN;
  d.txd_1.ft=TMI_FT_LONG;d.txd_1.own_mac=0x12;d.txd_1.no_ack=1;
  d.txd_1.hdr_format=TMI_HDR_FT_NOR_80211;
  d.txd_2.sub_type=SUBTYPE_BEACON;d.txd_2.bc_mc_pkt=1;
  switch(fault){
  case 1:d.txd_5.tx_status_2_host=1;break;
  case 2:d.txd_5.tx_status_2_mcu=1;break;
  case 3:d.txd_5.pid=1;break;
  case 4:d.txd_1.own_mac=0x11;break;
  case 5:d.txd_0.q_idx=0;break;
  case 6:d.txd_1.ft=0;break;
  case 7:d.txd_1.wlan_idx=1;break;
  case 8:d.txd_1.no_ack=0;break;
  case 9:d.txd_1.hdr_format=0;break;
  case 10:d.txd_2.frm_type=2;break;
  case 11:d.txd_2.sub_type=0;break;
  case 12:d.txd_2.bc_mc_pkt=0;break;
  case 13:d.txd_0.p_idx=1;break;
  }
  unsigned char unaligned[sizeof(d)+1];memcpy(unaligned+1,&d,sizeof(d));
  assert(wr_iot_ra2_no_host_txd(unaligned+1,sizeof(d))==(fault==0));
  for(unsigned n=0;n<sizeof(d);n++)assert(!wr_iot_ra2_no_host_txd(unaligned+1,n));
 }
 assert(!wr_iot_ra2_no_host_txd(NULL,100));
 puts("PASS actual vendor TXD bitfields: scoped no-status descriptor, unaligned copy, truncated input and host/MCU/PID/scope refusals; no packet ownership proof");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-ra2-txd-decode-') as scratch:
    src = Path(scratch) / 'test.c'
    exe = Path(scratch) / 'test'
    src.write_text(prefix + '\n'.join(parts) + tail)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                    '-I'+str(Path(__file__).resolve().parent), str(src), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
