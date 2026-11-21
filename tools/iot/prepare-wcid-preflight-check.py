#!/usr/bin/env python3
"""Extract checked WCID preflight; preserve target UINT8/USHORT widths."""
import argparse
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
s=(a.candidate/'hw_ctrl/cmm_asic_mt.c').read_text()
start=s.index('INT wr_iot_update_rx_wcid_checked(')
begin=s.index('\tif (wtbl_ctrl->wtbl_entry_cnt[0] > 0)',start)
end=s.index('// TODO: shiang-7603',begin)
body=s[begin:end]
assert 'WCID = ' not in body
assert body.count('return WR_IOT_WCID_NOT_WRITTEN;')==2
header=(a.candidate/'include/rtmp.h').read_text()
assert 'UINT8 wtbl_entry_cnt[4];' in header
prefix=r'''
#include <assert.h>
#define WR_IOT_WCID_NOT_WRITTEN -1
#define RT_DEBUG_ERROR 0
#define DBGPRINT(l,args) do{(void)(l);}while(0)
struct ctrl {unsigned char wtbl_entry_cnt[4];};
static int writes;
static int check(struct ctrl *wtbl_ctrl,unsigned short WCID){
'''
suffix=r'''
writes++;return 0;}
int main(void){struct ctrl c={{4}};
assert(check(&c,4)==-1&&!writes);assert(check(&c,65535)==-1&&!writes);
c.wtbl_entry_cnt[0]=0;assert(check(&c,0)==-1&&!writes);
c.wtbl_entry_cnt[0]=4;assert(check(&c,3)==0&&writes==1);
assert(check(&c,0)==0&&writes==2);return 0;}
'''
a.output.write_text(prefix+body+suffix,encoding='utf-8')
print('Extracted actual WCID range/PSE preflight; no hardware transaction claim')
