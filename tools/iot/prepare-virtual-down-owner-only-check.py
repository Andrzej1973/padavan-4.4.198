#!/usr/bin/env python3
"""Test actual rejected legacy DOWN case with untouched count/callback state."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
s=(a.candidate/'common/cmm_cfg.c').read_text();begin=s.index('case CMD_RTPRIV_IOCTL_VIRTUAL_INF_DOWN:')
case=s[begin:s.index('case CMD_RTPRIV_IOCTL_VIRTUAL_INF_GET:',begin)]
assert 'WR_IOT_OWNER_ONLY_DOWN' in case
prefix=r'''
#include <assert.h>
#include <stddef.h>
#define CMD_RTPRIV_IOCTL_VIRTUAL_INF_DOWN 1
#define NDIS_STATUS_FAILURE 1
struct adapter{unsigned int count;};
struct request{int (*close)(void *);};
static int callbacks;
static int close_radio(void *dev){(void)dev;callbacks++;return 0;}
static int dispatch(struct adapter *ad,struct request *r){(void)ad;(void)r;
 switch(CMD_RTPRIV_IOCTL_VIRTUAL_INF_DOWN){
'''
post=r'''
 }return 0;}
int main(void){struct adapter ad;struct request r={close_radio};
 unsigned int counts[]={0,1,2,~0U};
 for(unsigned int i=0;i<4;i++){
  ad.count=counts[i];assert(dispatch(&ad,&r)==1&&ad.count==counts[i]);
  assert(dispatch(&ad,NULL)==1&&ad.count==counts[i]);
 }
 assert(!callbacks);return 0;}
'''
a.output.write_text(prefix+case+post,encoding='utf-8')
print('Extracted actual rejected DOWN case; checked owner path tested separately')
