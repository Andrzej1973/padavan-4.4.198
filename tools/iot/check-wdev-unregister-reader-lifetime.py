#!/usr/bin/env python3
"""Demonstrate why actual vendor unregister is not a reader lifetime join.

PASS means the counterexample was reproduced, not safe callback retirement.
The WDS allocation must remain retained until a separate reader join is bound.
"""
import argparse
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('candidate', type=Path)
args = parser.parse_args()
source = (args.candidate / 'tx_rx/wdev.c').read_text()
start = source.index('INT rtmp_wdev_idx_unreg(')
end = source.index('\nINT rtmp_wdev_idx_reg(', start)
body = source[start:end]
rx = (args.candidate / 'tx_rx/wdev_rx.c').read_text()
load = 'wdev = pAd->wdev_list[wdev_idx];'
read = 'VLAN_Size = (wdev->VLAN_VID != 0) ? LENGTH_802_1Q : 0;'
load_at = rx.index(load)
read_at = rx.index(read, load_at)
assert read_at - load_at < 150, 'RX lifetime counterexample needs review'
rx_fragment = rx[load_at:read_at + len(read)]
# Execute the real synchronous unregister between an RX load and its next use.
# The object remains allocated: this test intentionally never triggers UAF.
code = r'''
#include <assert.h>
#include <stddef.h>
typedef int INT;
typedef unsigned long ULONG;
#define WDEV_NUM_MAX 2
#define RT_DEBUG_WARN 0
#define RT_DEBUG_ERROR 0
#define RT_DEBUG_OFF 0
#define DBGPRINT(level,args) do {} while (0)
struct wifi_dev {int wdev_type,wdev_idx,VLAN_VID;};
typedef struct {int irq_lock;struct wifi_dev *wdev_list[WDEV_NUM_MAX];} RTMP_ADAPTER;
static int held;
#define RTMP_INT_LOCK(lock,flags) do {(void)(lock);(flags)=0;assert(!held);held=1;} while(0)
#define RTMP_INT_UNLOCK(lock,flags) do {(void)(lock);(void)(flags);assert(held);held=0;} while(0)
''' + body + r'''
int main(void) {
 struct wifi_dev old={0,0,7},replacement={0,0,19};
 RTMP_ADAPTER adapter={0,{&old,NULL}};
 struct wifi_dev *wdev;
 unsigned int wdev_idx=0,VLAN_Size;
 RTMP_ADAPTER *pAd=&adapter;
 #define LENGTH_802_1Q 4
''' + load + r'''
 struct wifi_dev *captured=wdev;
 assert(rtmp_wdev_idx_unreg(&adapter,&old)==0);
 assert(!held && !adapter.wdev_list[0] && old.wdev_idx==WDEV_NUM_MAX);
 ''' + rx_fragment[rx_fragment.index('/* only MBssid'): ] + r'''
 assert(VLAN_Size==LENGTH_802_1Q && captured==&old && captured->VLAN_VID==7);
 adapter.wdev_list[0]=&replacement;
 assert(captured!=adapter.wdev_list[0] && captured->VLAN_VID==7);
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-wdev-reader-lifetime-') as tmp:
    c = Path(tmp) / 'check.c'
    binary = Path(tmp) / 'check'
    c.write_text(code)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                    str(c), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)
print('PASS counterexample: raw RX reference survives actual unregister and slot reuse; reader join still required')
