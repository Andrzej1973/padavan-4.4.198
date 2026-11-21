#!/usr/bin/env python3
"""Execute generated close ordering with injected hardware/join outcomes."""
import argparse
from pathlib import Path
import subprocess
import tempfile
import close_fixture_support as support

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('driver',type=Path);p.add_argument('--support',type=Path)
a=p.parse_args();here=Path(__file__).resolve().parent
source=(a.driver/'common/rtmp_init_inf.c').read_text()
f=support.body(source,'static INT wr_iot_checked_close_body(')
prefix=(here/'checked-close-host-fixture.c.in').read_text().split('@@CHECKED_CLOSE_FUNCTION@@')[0]
prefix=prefix.replace('static inline int mock_nettask_exit(void *ad){(void)ad;return 0;}',
                      'static int mock_nettask_exit(void *ad);')
prefix='#define MT_MAC 1\n'+support.prefix(prefix)
prefix=prefix.replace('#include "wr-iot-peer-legacy-close.inc"','')
stubs=r'''
static int order,qmac,qdata,qap,qoff,qglobal,qirq,qrelease,qctrl,commands;
static int rx_result,tail_fail,epoch_drift;
#define IS_MT7603(ad) ((ad)->chipCap.hif_type==HIF_MT)
#undef wr_iot_mt_radio_off_checked
#undef RTMP_OS_IRQ_RELEASE
#undef MCU_CTRL_EXIT
static int wr_iot_mt_prepare_close_rx(RTMP_ADAPTER *ad,const struct wr_iot_radio_ticket *t){
 assert(!held&&ad&&t);qmac=++order;ad->wr_iot_transition.mt_radio_off_stage=1;return 1;
}
static int wr_iot_nettask_data_exit(RTMP_ADAPTER *ad){assert(ad&&qmac&&!held);qdata=++order;return 0;}
static int wr_iot_ap_shutdown_before_radio_off(RTMP_ADAPTER *ad){
 assert(ad&&qdata&&!held);qap=++order;ap_calls++;return ap_result;
}
#define wr_iot_mlme_halt_checked(ad) (MlmeHalt(ad),TRUE)
static int mock_off(RTMP_ADAPTER *ad,const struct wr_iot_radio_ticket *t){
 assert(ad&&t&&!held&&qap);
 if(ad->wr_iot_transition.mt_radio_off_stage==5)return 0;
 if(ad->wr_iot_transition.mt_radio_off_stage==4)return 1;
 assert(ad->flags&fRTMP_ADAPTER_INTERRUPT_ACTIVE);
 qoff=++order;commands++;
 ad->wr_iot_transition.mt_radio_off_stage=radio_result?4:5;
 if(radio_result)ad->flags&=~fRTMP_ADAPTER_INTERRUPT_ACTIVE;
 return radio_result;
}
#define wr_iot_mt_radio_off_checked(ad,t) mock_off(ad,t)
static int mock_nettask_exit(void *ptr){
 RTMP_ADAPTER *ad=ptr;assert(!held);
 if(IS_MT7603(ad))assert(qoff&&ad->wr_iot_transition.mt_radio_off_stage==4);
 qglobal=++order;return rx_result;
}
static void mock_irq(RTMP_ADAPTER *ad,void *dev){
 (void)dev;assert(!held&&ad&&qglobal&&!rx_result);qirq=++order;
}
#define RTMP_OS_IRQ_RELEASE(ad,dev) mock_irq(ad,dev)
static int wr_iot_ap_release_after_join(RTMP_ADAPTER *ad,const struct wr_iot_radio_ticket *t){
 assert(!held&&ad&&t&&qirq&&qglobal&&qoff);
 assert(!(ad->flags&fRTMP_ADAPTER_INTERRUPT_IN_USE));
 assert(ad->wr_iot_transition.shutdown_stage==6);
 qrelease=++order;ad->wr_iot_transition.ap_cleanup_serial=t->serial;
 if(tail_fail)ad->wr_iot_peer_table_owner.transactions=1;
 return 1;
}
#define MCU_CTRL_EXIT(ad) ((void)(ad),qctrl=++order,(ad)->wr_iot_transition.epoch+=epoch_drift)
static void init(RTMP_ADAPTER *ad,struct wr_iot_radio_ticket *t){
 memset(ad,0,sizeof(*ad));wr_test_peer_fresh(ad);wr_iot_radio_transition_init(&ad->wr_iot_transition);
 ad->wr_iot_transition.phase=WR_RADIO_READY;
 assert(wr_iot_radio_begin_stop(&ad->wr_iot_transition,1,t));
 ad->chipCap.hif_type=HIF_MT;ad->infType=RTMP_DEV_INF_PCI;
 ad->flags=fRTMP_ADAPTER_INTERRUPT_ACTIVE|fRTMP_ADAPTER_INTERRUPT_IN_USE;
 order=qmac=qdata=qap=qoff=qglobal=qirq=qrelease=qctrl=commands=0;
 rx_result=tail_fail=epoch_drift=join_result=0;radio_result=ap_result=1;ap_calls=0;
}
'''
tests=r'''
int main(void){
 RTMP_ADAPTER ad;struct wr_iot_radio_ticket t;int started=0;
 init(&ad,&t);assert(wr_iot_checked_close_body(&ad,0,&t,&started)==0);
 assert(qmac<qdata&&qdata<qap&&qap<qoff&&qoff<qglobal&&qglobal<qirq&&qirq<qrelease&&qrelease<qctrl);
 assert(commands==1&&ap_calls==1&&ad.wr_iot_transition.shutdown_stage==2);
 assert(ad.wr_iot_transition.close_body_serial==t.serial&&ad.wr_iot_transition.close_body_epoch==t.epoch);
 struct wr_iot_radio_ticket next;
 assert(wr_iot_radio_finish(&ad.wr_iot_transition,&t,1));
 assert(wr_iot_radio_begin(&ad.wr_iot_transition,ad.wr_iot_transition.epoch,WR_RADIO_START,&next));
 assert(ad.wr_iot_transition.shutdown_stage==0&&ad.wr_iot_transition.mt_radio_off_stage==0);
 assert(ad.wr_iot_transition.close_body_serial==t.serial&&ad.wr_iot_transition.close_body_epoch==t.epoch);
 init(&ad,&t);radio_result=0;
 assert(wr_iot_checked_close_body(&ad,0,&t,&started)==1&&!qglobal&&!qirq&&!qrelease);
 assert(ad.wr_iot_transition.shutdown_stage==4&&commands==1);
 assert(!ad.wr_iot_transition.close_body_serial&&!ad.wr_iot_transition.close_body_epoch);
 assert(wr_iot_checked_close_body(&ad,0,&t,&started)==1&&commands==1&&ap_calls==1);
 init(&ad,&t);rx_result=1;
 assert(wr_iot_checked_close_body(&ad,0,&t,&started)==1&&!qirq&&!qrelease&&commands==1);
 rx_result=0;assert(wr_iot_checked_close_body(&ad,0,&t,&started)==0&&commands==1&&ap_calls==1);
 init(&ad,&t);ap_result=0;
 assert(wr_iot_checked_close_body(&ad,0,&t,&started)==1&&!qoff&&!qrelease);
 assert(wr_iot_checked_close_body(&ad,0,&t,&started)==1&&ap_calls==1);
 init(&ad,&t);tail_fail=1;
 assert(wr_iot_checked_close_body(&ad,0,&t,&started)==1&&qrelease&&ad.wr_iot_transition.shutdown_stage==6);
 assert(!ad.wr_iot_transition.close_body_serial&&!ad.wr_iot_transition.close_body_epoch);
 int old=qrelease;assert(wr_iot_checked_close_body(&ad,0,&t,&started)==1&&qrelease==old&&commands==1);
 init(&ad,&t);epoch_drift=1;
 assert(wr_iot_checked_close_body(&ad,0,&t,&started)==1);
 assert(ad.wr_iot_transition.shutdown_stage==6&&!ad.wr_iot_transition.close_body_serial);
 assert(!held);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-close-order-check-') as temporary:
    root=Path(temporary);(root/'check.c').write_text(prefix+stubs+f+tests)
    includes=['-I'+str(a.driver/'include')]
    if a.support:includes+=['-I'+str(a.support/'include')]
    subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
                    '-fno-pie','-no-pie',*includes,'-I'+str(here),str(root/'check.c'),'-o',str(root/'check')],check=True)
    subprocess.run([str(root/'check')],check=True)
print('PASS actual close ordering and partial-failure replay fences; mocked hardware/joins only')
