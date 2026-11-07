#!/usr/bin/env python3
"""Extract vendor lookup and demonstrate why address lookup is not a lease."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
if a.output.exists():
    p.error('new output required')
s = (a.candidate / 'mgmt/mgmt_entrytb.c').read_text()
anchor = 'MAC_TABLE_ENTRY *MacTableLookup(RTMP_ADAPTER *pAd, UCHAR *pAddr)'
if s.count(anchor) != 1:
    p.error('unique lookup required')
start = s.index(anchor)
end = s.index('\n}', start) + 2
body = s[start:end]
prefix = r'''
#include <assert.h>
#include <stddef.h>
#include <string.h>
typedef unsigned char UCHAR;
typedef unsigned long ULONG;
typedef struct entry {UCHAR Addr[6];int none,generation;struct entry *pNext;} MAC_TABLE_ENTRY;
typedef struct {struct {MAC_TABLE_ENTRY *Hash[1];} MacTab;} RTMP_ADAPTER;
#define MAC_ADDR_HASH_INDEX(a) ((void)(a),0)
#define MAC_ADDR_EQUAL(a,b) (memcmp((a),(b),6)==0)
#define IS_ENTRY_NONE(e) ((e)->none)
'''
suffix = r'''
int main(void){
 UCHAR addr[6]={1,2,3,4,5,6};RTMP_ADAPTER a={0};MAC_TABLE_ENTRY e={0};
 memcpy(e.Addr,addr,6);e.generation=1;a.MacTab.Hash[0]=&e;
 MAC_TABLE_ENTRY *saved=MacTableLookup(&a,addr);assert(saved==&e);
 /* Model delete/reallocate between lookup and callback lock acquisition. */
 e.none=1;a.MacTab.Hash[0]=NULL;
 e=(MAC_TABLE_ENTRY){.generation=2};memcpy(e.Addr,addr,6);a.MacTab.Hash[0]=&e;
 assert(saved==MacTableLookup(&a,addr)&&saved->generation==2);
 /* Even a fresh late lookup resolves the new association with same address. */
 assert(MacTableLookup(&a,addr)->generation!=1);
 a.MacTab.Hash[0]=NULL;assert(MacTableLookup(&a,addr)==NULL);
 return 0;
}
'''
a.output.write_text(prefix + body + suffix, encoding='utf-8')
print('Extracted lookup reuse witness; modeled interleaving, not a device race reproduction')
