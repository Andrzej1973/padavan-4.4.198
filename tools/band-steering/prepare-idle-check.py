#!/usr/bin/env python3
"""Compile the actual prepared idle case with mock driver collaborators."""
import argparse
from pathlib import Path
import re

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('probes', type=Path)
a = p.parse_args()
source = (a.source / 'trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/ap/ap_band_steering.c').read_text()
begin = source.index('\t\tcase WR_IDLE_QUERY: {')
end = source.index('\t\tcase CLI_ADD: {', begin)
case = source[begin:end]
calls = re.findall(r'\b([A-Za-z_]\w*)\s*\(', case)
allowed = {'if', 'sizeof', 'MacTableLookup', 'BndStrg_TableLookup', 'BndStrg_DeleteEntry', 'BndStrgSendMsg'}
if set(calls) - allowed:
    raise SystemExit('Unexpected operation in idle driver case')
declarations = (a.probes / 'mt76x3-abi.c').read_text().split('_Static_assert', 1)[0]
test = r'''
#include <assert.h>
#include <string.h>
#include <stdio.h>
#define WR_IDLE_QUERY 0x70
#define WR_IDLE_RSP 0x71
#define BND_STRG_MAX_TABLE_SIZE 64
#define BND_STRG_SUCCESS 0
#define BND_STRG_INVALID_ARG -9
typedef struct { int dummy; } MAC_TABLE_ENTRY;
typedef struct { UINT8 TableIndex; } BND_STRG_CLI_ENTRY, *PBND_STRG_CLI_ENTRY;
typedef struct { struct { struct { unsigned length; } data; } u; } RTMP_IOCTL_INPUT_STRUCT;
static int present, has_entry, index_value, delete_result, deleted, sent;
static BNDSTRG_MSG response;
static MAC_TABLE_ENTRY station;
static BND_STRG_CLI_ENTRY entry;
static MAC_TABLE_ENTRY *MacTableLookup(void *ad, UCHAR *mac) { (void)ad; (void)mac; return present ? &station : NULL; }
static PBND_STRG_CLI_ENTRY BndStrg_TableLookup(void *table, UCHAR *mac) {
    (void)table; (void)mac; entry.TableIndex = (UINT8)index_value; return has_entry ? &entry : NULL;
}
static int BndStrg_DeleteEntry(void *table, UCHAR *mac, unsigned index) {
    (void)table; (void)mac; assert(index == 0xff); ++deleted; return delete_result;
}
static int BndStrgSendMsg(void *ad, BNDSTRG_MSG *msg) { (void)ad; response = *msg; ++sent; return 0; }
static int exercise(BNDSTRG_MSG *msg, unsigned length, int Status) {
    void *pAd = NULL, *table = NULL;
    RTMP_IOCTL_INPUT_STRUCT request = {0}, *wrq = &request;
    request.u.data.length = length;
    switch (msg->Action) {
__CASE__
    default: return BND_STRG_INVALID_ARG;
    }
    return 0;
}
int main(void) {
    BNDSTRG_MSG msg = {0};
    msg.Action = WR_IDLE_QUERY; msg.data.idle.TableIndex = 7;
    msg.data.idle.Cookie = 0x12345678; msg.data.idle.Addr[0] = 2;
    has_entry = 1; index_value = 7;
    assert(exercise(&msg, sizeof(msg), 0) == 0 && response.data.idle.ReturnCode == 0 && deleted == 1);
    assert(response.Action == WR_IDLE_RSP && response.data.idle.Cookie == 0x12345678);
    assert(memcmp(response.data.idle.Addr, msg.data.idle.Addr, 6) == 0);
    present = 1; deleted = 0;
    assert(exercise(&msg, sizeof(msg), 0) == 0 && response.data.idle.ReturnCode == 1 && !deleted);
    present = 0; has_entry = 0;
    assert(exercise(&msg, sizeof(msg), 0) == 0 && response.data.idle.ReturnCode == 0 && !deleted);
    has_entry = 1; index_value = 8;
    assert(exercise(&msg, sizeof(msg), 0) == 0 && response.data.idle.ReturnCode == 2 && !deleted);
    index_value = 7; delete_result = -1;
    assert(exercise(&msg, sizeof(msg), 0) == 0 && response.data.idle.ReturnCode == 2 && deleted == 1);
    sent = 0;
    assert(exercise(&msg, sizeof(msg) - 1, 0) == BND_STRG_INVALID_ARG && !sent);
    assert(exercise(&msg, sizeof(msg), 1) == BND_STRG_INVALID_ARG && !sent);
    msg.data.idle.TableIndex = 64;
    assert(exercise(&msg, sizeof(msg), 0) == BND_STRG_INVALID_ARG && !sent);
    msg.data.idle.TableIndex = 7; msg.data.idle.Cookie = 0;
    assert(exercise(&msg, sizeof(msg), 0) == BND_STRG_INVALID_ARG && !sent);
    puts("PASS: actual prepared idle driver case, presence guards, non-deauth operations and echoed cookie; collaborators mocked");
    return 0;
}
'''.replace('__CASE__', case)
(a.probes / 'check-idle-driver.c').write_text(declarations + test, encoding='utf-8')
print('Generated mocked check from the actual prepared driver case')
