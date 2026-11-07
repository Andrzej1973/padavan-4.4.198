#!/usr/bin/env python3
"""Execute generated err6 block with firmware-stop/join fault injection."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
s=(a.candidate/'common/rtmp_init_inf.c').read_text();start=s.index('err6:\n');end=s.index('\nerr5:',start);block=s[start:end].replace('err6:\n','',1)
assert block.index('FwExit')<block.index('RtmpNetTaskExit')<block.index('MCU_CTRL_EXIT')
code=r'''
#include <assert.h>
#define MT7603 1
#define RTMP_PCI_SUPPORT 1
#define FALSE 0
#define NDIS_STATUS_SUCCESS 0
typedef struct adapter ADAPTER;
struct adapter {struct {void (*FwExit)(ADAPTER *);} chipOps;};
static int stage,refuse,cleaned,dma_refuse;
static void stop(ADAPTER *a){assert(a&&stage==0);stage=1;}
static int RtmpNetTaskExit(ADAPTER *a){assert(a&&stage==1);stage=2;return refuse;}
static int wr_iot_mcu_dma_disabled_idle(ADAPTER *a){assert(a&&stage==2);return !dma_refuse;}
#define MCU_CTRL_EXIT(a) do{assert((a)&&stage==2&&!refuse);cleaned++;stage=3;}while(0)
static int unwind(ADAPTER *pAd){
'''+block+r'''
return 1;}
int main(void){ADAPTER a={{stop}};
refuse=1;assert(!unwind(&a)&&stage==2&&!cleaned);
stage=0;refuse=0;dma_refuse=1;assert(!unwind(&a)&&stage==2&&!cleaned);
stage=0;dma_refuse=0;assert(unwind(&a)&&stage==3&&cleaned==1);
return 0;}
'''
with tempfile.TemporaryDirectory(prefix='wr-mcu-init-join-') as d:
 c=Path(d)/'check.c';c.write_text(code)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',d+'/check'],check=True);subprocess.run([d+'/check'],check=True)
print('PASS actual generated err6 ordering and refusal before MCU cleanup; kernel IRQ/RX join mocked')
