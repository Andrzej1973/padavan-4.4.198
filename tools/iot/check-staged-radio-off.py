#!/usr/bin/env python3
"""Run generated early-RX/full-OFF bodies through existing MMIO fault fixtures."""
import argparse
import importlib.util
from pathlib import Path
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__);p.add_argument('driver',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('radio_fixture',here/'check-mt7603-checked-off.py')
fixture=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixture)
text=(a.driver/'hw_ctrl/cmm_asic_mt.c').read_text()
def body(name):
    start=text.index('BOOLEAN '+name+'(');return text[start:text.index('\n}',start)+2]
prefix=fixture.PREFIX.replace('wr_iot_send_radio_off_checked(RTMP_ADAPTER *p) {',
    'wr_iot_send_radio_off_checked(RTMP_ADAPTER *p,const struct wr_iot_radio_ticket *ticket) {\n (void)ticket;')
extra=r'''
static void check_rx_prefix(void){
 RTMP_ADAPTER p=fresh();struct wr_iot_radio_ticket t={WR_RADIO_CLOSE,42};active=&p;
#ifdef LOAD_FW_ONE_TIME
 require(!wr_iot_mt_prepare_close_rx(&p,&t),"one-time RX preparation refusal");
 require(!p.queue_calls&&!p.mac_calls,"no early mutation in unsupported mode");
#else
 require(wr_iot_mt_prepare_close_rx(&p,&t),"early RX preparation");
 require(p.wr_iot_transition.mt_radio_off_stage==1,"early RX receipt");
 require(!p.cmd_calls&&!p.poll_calls&&!p.pdma_calls&&!p.irq_calls&&p.dma==3,"MCU DMA/IRQ untouched");
 require(wr_iot_mt_prepare_close_rx(&p,&t)&&p.mac_calls==1,"RX preparation retry does not repeat writes");
 require(wr_iot_mt_radio_off_checked(&p,&t)&&p.cmd_calls==1,"OFF continues after early RX preparation");
#endif
}
'''
suffix=fixture.SUFFIX.replace('int main(void) {',extra+'\nint main(void) {\n check_rx_prefix();',1)
source=prefix+body('wr_iot_mt_prepare_close_rx')+'\n'+body('wr_iot_mt_radio_off_checked')+suffix
with tempfile.TemporaryDirectory(prefix='wr-staged-radio-check-') as temporary:
    root=Path(temporary);(root/'check.c').write_text(source)
    for flags in ([],['-DLOAD_FW_ONE_TIME=1']):
        subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
                        '-fno-pie','-no-pie',*flags,str(root/'check.c'),'-o',str(root/'check')],check=True)
        subprocess.run([str(root/'check')],check=True)
print('PASS generated RX preparation/OFF fault injection and one-time refusal; mocked MMIO only')
