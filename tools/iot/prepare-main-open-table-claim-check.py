#!/usr/bin/env python3
"""Extract open admission seams and real client/dispatch, not full radio init."""
import argparse,re
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
r=a.candidate
outer=(r/'os/linux/rt_main_dev.c').read_text();st=outer.index('int rt28xx_open(VOID *dev)');outer=outer[st:outer.index('\n}',st)+2]
begin='if(wr_iot_peer_open_call(pAd,&wr_claim,WR_PEER_OPEN_BEGIN)!=NDIS_STATUS_SUCCESS)return -EBUSY;'
for action in ['DiagProcInit(pAd);','load_dev_l1profile(pAd)','RtmpOSIRQRequest(net_dev);','RTMP_DRIVER_IRQ_INIT(pAd);']:
 assert outer.index(begin)<outer.index(action)
assert 'rt28xx_init(pAd, mac, hostname,&wr_claim)' in outer
assert outer.index('WR_PEER_OPEN_FAIL')<outer.index('RTMP_DRIVER_IRQ_RELEASE(pAd);')
core=(r/'common/rtmp_init_inf.c').read_text();st=core.index('int rt28xx_init(');core=core[st:core.index('\nVOID RTMPDrvOpen(')]
check='if(wr_iot_peer_open_call(pAd,&wr_request,WR_PEER_OPEN_CONFIG_CHECK)!=NDIS_STATUS_SUCCESS)return FALSE;'
assert core.index(check)<core.index('hif_sys_init(')<core.index('rtmp_cfg_init(')
assert core.index('wr_iot_peer_open_release_config(')<core.index('APStartUp(pAd);')
header=(r/'include/rt_os_net.h').read_text()
field=re.search(r'^int \(\*rt28xx_init\)[^;]+;',header,re.M).group()
assert 'const struct wr_iot_peer_open_request *wr_claim' in field
fixture=Path(__file__).with_name('check-peer-open-dispatch.c').read_text().replace('int main(void){','static int dispatch_checks(void){',1)
define=re.search(r'^#define CMD_RTPRIV_IOCTL_PEER_OPEN_OWNER .+$',(r/'include/rtmp_cmd.h').read_text(),re.M).group()
shim=r'''
typedef void VOID;typedef char RTMP_STRING;
#define EBUSY 16
static int effects,inner_calls;
static int RTMP_COM_IoctlHandle(void *ad,void *wrq,int cmd,unsigned short sub,void *data,ULONG size){
 assert(!wrq&&!sub&&cmd==CMD_RTPRIV_IOCTL_PEER_OPEN_OWNER);
 return wr_iot_peer_open_dispatch(ad,data,size);
}
#include "wr-iot-peer-open-client.inc"
'''
seams='''
static int core_seam(VOID *pAd,RTMP_STRING *mac,RTMP_STRING *host,const struct wr_iot_peer_open_request *wr_claim){
 struct wr_iot_peer_open_request wr_request;
 (void)mac;(void)host;
 if(!pAd||!wr_claim)return 0;wr_request=*wr_claim;
'''+check+'''
 inner_calls++;
 return wr_iot_peer_open_release_config(pAd,&wr_request)==NDIS_STATUS_SUCCESS;
}
typedef struct {'''+field+'''} MOCK_OPS;
static int outer_seam(VOID *pAd,void *net_dev){
 struct wr_iot_peer_open_request wr_claim={WR_IOT_PEER_OPEN_REQUEST_VERSION,WR_PEER_OPEN_BEGIN,net_dev,0};
 MOCK_OPS ops={core_seam};
'''+begin+'''
 effects++;
 return ops.rt28xx_init(pAd,NULL,NULL,&wr_claim)?0:-1;
}
'''
tail=r'''
int main(void){assert(!dispatch_checks());setup();effects=inner_calls=0;
 a.MacTab.Content[1].kind=1;
 assert(outer_seam(&a,&device)==-EBUSY&&!effects&&!inner_calls&&!a.wr_iot_peer_table_owner.active);
 a.MacTab.Content[1].kind=0;
 assert(!outer_seam(&a,&device)&&effects==1&&inner_calls==1&&!a.wr_iot_peer_table_owner.active);
 setup();assert(wr_iot_peer_open_call(&a,&request,WR_PEER_OPEN_BEGIN)==0);
 assert(wr_iot_peer_open_call(&a,&request,WR_PEER_OPEN_CONFIG_CHECK)==0);
 {struct wr_iot_peer_open_request stale=request;stale.serial++;
 assert(!core_seam(&a,NULL,NULL,&stale));}
 assert(wr_iot_peer_open_call(&a,&request,WR_PEER_OPEN_FAIL)==0&&a.wr_iot_peer_table_owner.retained);
 assert(outer_seam(&a,&device)==-EBUSY&&effects==1&&inner_calls==1);
 assert(wr_iot_peer_open_call(&a,&request,WR_PEER_OPEN_CONFIG_CHECK)==1);
 assert(wr_iot_peer_open_release_config(&a,&request)==1);
 return 0;}
'''
# Keep seam fixture formatting independent of vendor indentation.
seams=seams.replace('if(!pAd||!wr_claim)return 0;wr_request=*wr_claim;',
 'if(!pAd||!wr_claim)return 0;\n wr_request=*wr_claim;')
shim='#define FALSE 0\n'+shim
a.output.write_text(define+'\n'+fixture+shim+seams+tail,encoding='utf-8')
print('Extracted admission seams/client/dispatch and init ops field; full init/OS_ABL binary uncompiled')
