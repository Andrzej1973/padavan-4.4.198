#!/usr/bin/env python3
"""Extract actual internal ioctl case around tested dispatch; mock outer ioctl."""
import argparse,re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
s=(a.candidate/'common/cmm_cfg.c').read_text()
start=s.index('case CMD_RTPRIV_IOCTL_PEER_OPEN_OWNER:')
end=s.index('case CMD_RTPRIV_IOCTL_NETDEV_GET:',start);case=s[start:end]
header=(a.candidate/'include/rtmp_cmd.h').read_text()
define=re.search(r'^#define CMD_RTPRIV_IOCTL_PEER_OPEN_OWNER .+$',header,re.M).group()
fixture=Path(__file__).with_name('check-peer-open-dispatch.c').read_text()
fixture=fixture.replace('int main(void){','static int dispatch_cases(void){',1)
tail='''
static int core_case(int cmd,void *wrq,unsigned short subcmd,void *pData,ULONG Data){
 RTMP_ADAPTER *pAd=&a;
 switch(cmd){
'''+case+'''
 }return NDIS_STATUS_FAILURE;
}
int main(void){
 assert(!dispatch_cases());setup();
 assert(core_case(CMD_RTPRIV_IOCTL_PEER_OPEN_OWNER,&device,0,&request,sizeof request)==1&&!locks);
 assert(core_case(CMD_RTPRIV_IOCTL_PEER_OPEN_OWNER,NULL,1,&request,sizeof request)==1&&!locks);
 assert(core_case(CMD_RTPRIV_IOCTL_PEER_OPEN_OWNER,NULL,0,NULL,sizeof request)==1&&!locks);
 assert(core_case(CMD_RTPRIV_IOCTL_PEER_OPEN_OWNER,NULL,0,&request,sizeof request-1)==1&&!locks);
 assert(core_case(0,NULL,0,&request,sizeof request)==1&&!locks);
 assert(!core_case(CMD_RTPRIV_IOCTL_PEER_OPEN_OWNER,NULL,0,&request,sizeof request)&&request.serial&&!held);
 request.action=WR_PEER_OPEN_FAIL;
 assert(!core_case(CMD_RTPRIV_IOCTL_PEER_OPEN_OWNER,NULL,0,&request,sizeof request)&&a.wr_iot_peer_table_owner.retained);
 return 0;
}
'''
dispatch_source=(a.candidate/'include/wr-iot-peer-open-dispatch.inc').read_text()
if 'wr_iot_peer_close_executor_idle' in dispatch_source:
 fixture=fixture.replace('#include "peer-open-owner.h"','#include "peer-open-owner.h"\n#include "peer-close-executor.h"')
 tail=tail.replace('assert(!dispatch_cases());setup();', '''assert(!dispatch_cases());setup();
 assert(wr_iot_peer_close_executor_enter(&a.wr_iot_peer_close_executor,WR_PEER_CLOSE_CHECKED,8));
 assert(dispatch()==1&&!request.serial);
 assert(wr_iot_peer_close_executor_leave(&a.wr_iot_peer_close_executor,WR_PEER_CLOSE_CHECKED,8,0,1));
 assert(dispatch()==1&&!request.serial);
 setup();''')
if 'wr_iot_peer_legacy_close_state' in dispatch_source:
 tail=tail.replace('assert(!dispatch_cases());setup();', '''assert(!dispatch_cases());setup();
 a.wr_iot_peer_legacy_close_state=1;
 assert(dispatch()==1&&!request.serial&&!a.wr_iot_peer_table_owner.active);
 assert(a.wr_iot_peer_legacy_close_state==1);
 setup();a.wr_iot_peer_legacy_close_state=2;a.wr_iot_peer_table_owner.closed=1;
 request.device=&other;assert(dispatch()==1&&a.wr_iot_peer_legacy_close_state==2);
 request.device=&device;assert(!dispatch()&&request.serial);
 assert(!a.wr_iot_peer_legacy_close_state&&!a.wr_iot_peer_table_owner.closed);
 setup();''')
a.output.write_text(define+'\n'+fixture+tail,encoding='utf-8')
print('Extracted internal ioctl case; full core handler and OS_ABL binary not compiled')
