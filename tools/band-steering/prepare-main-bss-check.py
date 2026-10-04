#!/usr/bin/env python3
"""Extract actual prepared legacy admission macro and RSSI function for fixtures."""
import argparse
from pathlib import Path
import re

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('probes', type=Path)
a = p.parse_args()
d = a.source / 'trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x2'
h = (d / 'include/band_steering.h').read_text()
s = (d / 'ap/ap_band_steering.c').read_text()
auth = (d / 'ap/ap_auth.c').read_text()
auth_call = 'BND_STRG_CHECK_CONNECTION_REQ(\tpAd,\n\t\t\t\t\t\t\t\t\t\twdev,'
if auth.count(auth_call) != 1:
    raise ValueError('Authentication must pass the resolved BSS device')
start = h.index('#define BND_STRG_CHECK_CONNECTION_REQ(')
macro = h[start:h.index('\n#ifdef BND_STRG_DBG', start)]
body = s[s.index('BOOLEAN BndStrg_IsClientStay('):s.index('\nINT BndStrg_MsgHandle(')]
if 'wr_bss_wdev->func_idx != MAIN_MBSSID' not in macro or 'pEntry->wdev->func_idx != MAIN_MBSSID' not in body:
    raise ValueError('Prepared main-BSS guards missing')
allowed = {'BndStrg_IsClientStay', 'if', 'sizeof', 'RTMPAvgRssi', 'COPY_MAC_ADDR', 'BND_STRG_DBGPRINT',
           'YLW', 'PRINT_MAC', 'RtmpOSWrielessEventSend', 'TableEntryDel'}
code = re.sub(r'/\*.*?\*/', '', body, flags=re.S)
code = re.sub(r'"(?:\\.|[^"\\])*"', '""', code)
calls = set(re.findall(r'\b([A-Za-z_]\w*)\s*\(', code))
if calls - allowed:
    raise ValueError('Unexpected kick function calls: ' + repr(calls - allowed))
declarations = (a.probes / 'mt76x2-abi.c').read_text().split('_Static_assert', 1)[0]
test = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define TRUE 1
#define FALSE 0
#define MAIN_MBSSID 0
#define RSSI_0 0
#define RSSI_1 1
#define RSSI_2 2
#define BAND_5G 1
#define fBND_STRG_CND_5G_RSSI 1
#define CLI_DEL 3
#define BND_STRG_MAX_TABLE_SIZE 64
#define RT_WLAN_EVENT_CUSTOM 0
#define OID_BNDSTRG_MSG 0x950
#define COPY_MAC_ADDR(a,b) memcpy(a,b,6)
#define BND_STRG_DBGPRINT(level,args) do {} while (0)
struct wifi_dev { int func_idx; };
struct entry { struct wifi_dev *wdev; int RssiSample; UCHAR Addr[6]; };
typedef struct entry *PMAC_TABLE_ENTRY;
struct ops { void (*TableEntryDel)(void *, UCHAR *, unsigned); };
struct table { struct { unsigned ConditionCheck; } AlgCtrl; int Band, RssiLow; struct ops *Ops; };
typedef struct table *PBND_STRG_CLI_TABLE;
struct adapter { int unused; void *net_dev; };
typedef struct adapter *PRTMP_ADAPTER;
static struct table fixture_table;
#define P_BND_STRG_TABLE (&fixture_table)
static int checked, converted, averaged, sent, deleted;
static CHAR ConvertToRssi(PRTMP_ADAPTER ad, CHAR rssi, int chain) {
    (void)ad; (void)chain; ++converted; return rssi;
}
static BOOLEAN BndStrg_CheckConnectionReq(PRTMP_ADAPTER ad, UCHAR *mac, unsigned frame, CHAR *rssi) {
    (void)ad; (void)mac; (void)frame; (void)rssi; ++checked; return FALSE;
}
static CHAR RTMPAvgRssi(PRTMP_ADAPTER ad, int *rssi) { (void)ad; ++averaged; return (CHAR)*rssi; }
static void RtmpOSWrielessEventSend(void *dev, int kind, int oid, void *unused, UCHAR *msg, unsigned size) {
    BNDSTRG_MSG *m = (BNDSTRG_MSG *)msg;
    (void)dev; (void)kind; (void)unused;
    assert(oid == 0x950 && size == sizeof(*m) && m->Action == CLI_DEL); ++sent;
}
static void remove_entry(void *t, UCHAR *mac, unsigned index) {
    (void)t; (void)mac; assert(index == 64); ++deleted;
}
__MACRO__
__BODY__
static BOOLEAN admission(PRTMP_ADAPTER ad, struct wifi_dev *wdev) {
    UCHAR mac[6] = {2}; BOOLEAN result = FALSE;
    BND_STRG_CHECK_CONNECTION_REQ(ad, wdev, mac, 3, -60, -61, -62, &result);
    return result;
}
int main(void) {
    struct adapter ad = {0}; struct wifi_dev main = {0}, guest = {1};
    struct ops ops = {remove_entry}; struct entry entry = {&guest, -90, {2}};
    fixture_table.AlgCtrl.ConditionCheck = 1; fixture_table.Band = 1;
    fixture_table.RssiLow = -70; fixture_table.Ops = &ops;
    { UCHAR mac[6] = {2}; BOOLEAN result = FALSE;
      BND_STRG_CHECK_CONNECTION_REQ(&ad, NULL, mac, 3, -60, -61, -62, &result);
      assert(result && !checked); }
    assert(admission(&ad, &guest) && !checked);
    assert(admission(&ad, NULL) && !checked);
    assert(!admission(&ad, &main) && checked == 1 && converted == 12);
    assert(BndStrg_IsClientStay(&ad, &entry) && !averaged && !sent && !deleted);
    entry.wdev = NULL;
    assert(BndStrg_IsClientStay(&ad, &entry) && !averaged);
    assert(BndStrg_IsClientStay(&ad, NULL) && !averaged);
    entry.wdev = &main;
    assert(!BndStrg_IsClientStay(&ad, &entry) && averaged == 1 && sent == 1 && deleted == 1);
    entry.RssiSample = -60;
    assert(BndStrg_IsClientStay(&ad, &entry) && averaged == 2 && sent == 1 && deleted == 1);
    puts("PASS actual legacy main-BSS admission and guest/no-wdev RSSI isolation");
    return 0;
}
'''
(a.probes / 'main-bss-check.c').write_text(declarations + test.replace('__MACRO__', macro).replace('__BODY__', body))

