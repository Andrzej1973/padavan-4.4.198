#!/usr/bin/env python3
"""Extract actual PCI probe work-join expressions; no device or kernel IO."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
if a.output.exists():
    p.error('New output required')
source = (a.candidate / 'os/linux/pci_main_dev.c').read_text(encoding='utf-8')
if source.count('void *pAd = NULL, *handle;') != 1:
    p.error('Changed PCI probe adapter declaration')
start = source.index('err_out_free_netdev:')
end = source.index('/* Attach failed after pci_set_drvdata', start)
fragment = source[start:end]
fragment = fragment[fragment.index('\n') + 1:]
if fragment.count('cancel_delayed_work_sync(') != 1 or fragment.count('cancel_work_sync(') != 2:
    p.error('Changed probe work-join sequence')
prefix = '''#include <assert.h>
#include <stdio.h>
struct work_struct { int id; };
struct delayed_work { int id; };
typedef struct { struct delayed_work wr_iot_main_recovery_reap_work;
 struct work_struct wr_iot_main_recovery_work,wr_iot_aux_family_retry_work;
} RTMP_ADAPTER,*PRTMP_ADAPTER;
static RTMP_ADAPTER adapter;static int calls;
static void cancel_delayed_work_sync(struct delayed_work *work){
 assert(!calls&&work==&adapter.wr_iot_main_recovery_reap_work);calls++;
}
static void cancel_work_sync(struct work_struct *work){
 assert(calls==1?work==&adapter.wr_iot_main_recovery_work:
        calls==2&&work==&adapter.wr_iot_aux_family_retry_work);calls++;
}
static void probe_unwind(void *pAd){
'''
tail = '''}
int main(void){probe_unwind(&adapter);assert(calls==3);
 puts("PASS actual void-adapter PCI probe work joins: typed targets and ordering; cancellation injected");return 0;}
'''
a.output.write_text(prefix + fragment + tail, encoding='utf-8', newline='\n')
print('Extracted actual PCI probe work joins; kernel cancellation injected')
