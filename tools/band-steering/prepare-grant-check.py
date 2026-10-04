#!/usr/bin/env python3
"""Exercise the actual prepared read-only driver cases with mock tables."""
import argparse
from pathlib import Path
import re

parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
parser.add_argument('probes', type=Path)
args = parser.parse_args()
for radio in ('mt76x2', 'mt76x3'):
    src = (args.source / ('trunk/linux-4.4.x/drivers/net/wireless/mediatek/' + radio + '/ap/ap_band_steering.c')).read_text()
    start = src.index('\t\tcase 0x72: {')
    end = src.index('\t\tcase CLI_ADD:', start)
    case = src[start:end]
    calls = set(re.findall(r'\b([A-Za-z_]\w*)\s*\(', case))
    allowed = {'if', 'sizeof', 'COPY_MAC_ADDR', 'TableLookup', 'D_BndStrgSendMsg',
               'BndStrg_TableLookup', 'BndStrgSendMsg'}
    if calls - allowed:
        raise ValueError('Unexpected operation in grant query: ' + repr(calls - allowed))
    declarations = (args.probes / (radio + '-abi.c')).read_text().split('_Static_assert', 1)[0]
    legacy = radio == 'mt76x2'
    state_enum = ''
    if not legacy:
        header = (args.source / ('trunk/linux-4.4.x/drivers/net/wireless/mediatek/' + radio + '/include/band_steering_def.h')).read_text()
        state_enum = re.search(r'enum BND_STRG_STA_STATE\s*\{.*?\};', header, re.S).group(0)
    wrapper = ''
    wrapper_tests = ''
    if legacy:
        wrapper = src[src.index('INT BndStrg_MsgHandle('):src.index('\nINT D_BndStrgSendMsg(')]
        if 'if (copy_from_user(' not in wrapper:
            raise ValueError('Legacy copy guard missing')
        wrapper_tests = '''
    RTMP_IOCTL_INPUT_STRUCT q = {0};
    q.u.data.length = sizeof(msg); q.u.data.pointer = &msg;
    sent = dispatched = 0; copy_failure = 1;
    assert(BndStrg_MsgHandle(NULL, &q) == BND_STRG_INVALID_ARG && !sent && !dispatched);
    copy_failure = 0; q.u.data.length--;
    assert(BndStrg_MsgHandle(NULL, &q) == BND_STRG_INVALID_ARG && !dispatched);
    q.u.data.length++; msg.Time = 9; msg.TalbeIndex = 7;
    assert(BndStrg_MsgHandle(NULL, &q) == BND_STRG_SUCCESS && dispatched == 1 && sent == 1);
'''
    test = r'''
#include <assert.h>
#include <string.h>
#include <stdio.h>
#define COPY_MAC_ADDR(a,b) memcpy((a),(b),6)
#define BND_STRG_MAX_TABLE_SIZE 64
#define BND_STRG_SUCCESS 0
#define BND_STRG_INVALID_ARG -9
#define BND_STRG_NOT_INITIALIZED -8
#define FALSE 0
typedef void *PRTMP_ADAPTER;
typedef int INT;
__STATEENUM__
typedef struct { UINT8 TableIndex; int BndStrg_Sta_State; } BND_STRG_CLI_ENTRY, *PBND_STRG_CLI_ENTRY;
typedef struct { struct { struct { unsigned length; void *pointer; } data; } u; } RTMP_IOCTL_INPUT_STRUCT;
struct ops { PBND_STRG_CLI_ENTRY (*TableLookup)(void *, UCHAR *); void (*MsgHandle)(void *, BNDSTRG_MSG *); };
typedef struct { int bInitialized; struct ops *Ops; } TABLE, *PBND_STRG_CLI_TABLE;
static int has_entry, index_value, state_value, sent, dispatched, copy_failure;
static BNDSTRG_MSG response;
static BND_STRG_CLI_ENTRY entry;
static PBND_STRG_CLI_ENTRY lookup(void *table, UCHAR *mac) {
    (void)table; (void)mac; entry.TableIndex = (UINT8)index_value; entry.BndStrg_Sta_State = state_value;
    return has_entry ? &entry : NULL;
}
__LOOKUP__
__SEND__
static int exercise(BNDSTRG_MSG *msg, unsigned length, int Status);
static void dispatch(void *ad, BNDSTRG_MSG *msg) { (void)ad; dispatched++; (void)exercise(msg, sizeof(*msg), 0); }
static struct ops operations = {lookup, dispatch};
static TABLE mock_table = {1, &operations};
#define P_BND_STRG_TABLE (&mock_table)
__COPY__
__WRAPPER__
static int exercise(BNDSTRG_MSG *msg, unsigned length, int Status) {
    void *pAd = NULL; TABLE *table = &mock_table;
    RTMP_IOCTL_INPUT_STRUCT request = {0}, *wrq = &request;
    (void)wrq; (void)Status; request.u.data.length = length;
    switch (msg->Action) {
__CASE__
    default: return BND_STRG_INVALID_ARG;
    }
    return 0;
}
int main(void) {
    BNDSTRG_MSG msg = {0}; msg.Action = 0x72;
    __REQUEST__
    assert(exercise(&msg, sizeof(msg), 0) == 0 && sent == 1 && __STATE__ == 0);
    assert(response.Action == 0x73 && __COOKIE__ == 9 && __INDEX__ == 7);
    assert(memcmp(__ADDR__, __INPUTADDR__, 6) == 0);
    has_entry = 1; index_value = 7;
    assert(exercise(&msg, sizeof(msg), 0) == 0 && __STATE__ == 1);
    __EXTRA__
    __INVALID__
    __WRAPPER_TESTS__
    puts("PASS: actual __RADIO__ grant query, absence/presence, correlation and invalid requests; no table mutation");
    return 0;
}
'''
    if legacy:
        replacements = {
            '__LOOKUP__': '',
            '__SEND__': 'static int D_BndStrgSendMsg(void *ad, BNDSTRG_MSG *msg) { (void)ad; response = *msg; ++sent; return 0; }',
            '__COPY__': 'static int copy_from_user(void *to, void *from, unsigned n) { if (copy_failure) return 1; memcpy(to, from, n); return 0; }',
            '__REQUEST__': 'msg.TalbeIndex = 7; msg.Time = 9; msg.Addr[0] = 2;',
            '__STATE__': 'response.ReturnCode', '__COOKIE__': 'response.Time', '__INDEX__': 'response.TalbeIndex',
            '__ADDR__': 'response.Addr', '__INPUTADDR__': 'msg.Addr', '__EXTRA__': '',
            '__INVALID__': '''sent = 0; msg.TalbeIndex = 64;
    assert(exercise(&msg, sizeof(msg), 0) == 0 && !sent);
    msg.TalbeIndex = 7; msg.Time = 0;
    assert(exercise(&msg, sizeof(msg), 0) == 0 && !sent);''',
        }
    else:
        replacements = {
            '__LOOKUP__': 'static PBND_STRG_CLI_ENTRY BndStrg_TableLookup(void *table, UCHAR *mac) { return lookup(table, mac); }',
            '__SEND__': 'static int BndStrgSendMsg(void *ad, BNDSTRG_MSG *msg) { (void)ad; response = *msg; ++sent; return 0; }',
            '__COPY__': '',
            '__REQUEST__': 'msg.data.idle.TableIndex = 7; msg.data.idle.Cookie = 9; msg.data.idle.Addr[0] = 2;',
            '__STATE__': 'response.data.idle.ReturnCode', '__COOKIE__': 'response.data.idle.Cookie',
            '__INDEX__': 'response.data.idle.TableIndex', '__ADDR__': 'response.data.idle.Addr',
            '__INPUTADDR__': 'msg.data.idle.Addr',
            '__EXTRA__': '''state_value = BNDSTRG_STA_ASSOC;
    assert(exercise(&msg, sizeof(msg), 0) == 0 && response.data.idle.ReturnCode == 3);
    state_value = BNDSTRG_STA_INIT; index_value = 8;
    assert(exercise(&msg, sizeof(msg), 0) == 0 && response.data.idle.ReturnCode == 2);''',
            '__INVALID__': '''sent = 0;
    assert(exercise(&msg, sizeof(msg) - 1, 0) == BND_STRG_INVALID_ARG && !sent);
    assert(exercise(&msg, sizeof(msg), 1) == BND_STRG_INVALID_ARG && !sent);
    msg.data.idle.TableIndex = 64;
    assert(exercise(&msg, sizeof(msg), 0) == BND_STRG_INVALID_ARG && !sent);
    msg.data.idle.TableIndex = 7; msg.data.idle.Cookie = 0;
    assert(exercise(&msg, sizeof(msg), 0) == BND_STRG_INVALID_ARG && !sent);
    (void)operations; (void)copy_failure;''',
        }
    replacements.update({'__CASE__': case, '__WRAPPER__': wrapper,
                         '__WRAPPER_TESTS__': wrapper_tests, '__RADIO__': radio,
                         '__STATEENUM__': state_enum})
    for key, value in replacements.items():
        test = test.replace(key, value)
    with (args.probes / ('check-grant-' + radio + '.c')).open('w', encoding='utf-8', newline='\n') as out:
        out.write(declarations + test)
