#!/usr/bin/env python3
"""Execute composed RRB capture and stamped FT consumer with explicit actors."""
import argparse,contextlib,io,runpy,subprocess,sys,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
# Reuse the established full native callback fixtures and all their assertions.
argv=sys.argv[:];sys.argv=[str(here/'check-ft-parser-composition.py'),str(a.source)]
try:
 with contextlib.redirect_stdout(io.StringIO()):data=runpy.run_path(sys.argv[0])
finally:sys.argv=argv
mlme=runpy.run_path(str(here/'assoc-generation-composition.py'))['compose']({},a.source,here)['common/mlme.c']
module=runpy.run_path(str(here/'ft-enqueue-generation-composition.py'))
_,prototype=module['compose'](mlme)
prepared=module['bind_ft'](data['text'],prototype)
def function(name):
 start=prepared.index('VOID '+name+'(');return prepared[start:prepared.index('\n}',start)+2]
assert prepared.count('wr_ft_peer_capture_locked(')==1
assert prepared.count('wr_ft_peer_enter_locked(')==1 and prepared.count('wr_ft_peer_leave_locked(')==1
try:module['bind_ft'](prepared,prototype)
except ValueError:pass
else:raise AssertionError('duplicate binding accepted')

def types(text):
 text="#define MAC_ADDR_LEN 6\n"+text
 text=text.replace('#include <string.h>','#include <string.h>\n#include "peer-table-owner.h"')
 text=text.replace('unsigned wcid;int client','unsigned assoc_gen,wcid;int client')
 text=text.replace('unsigned int wcid;int func_tb_idx','unsigned int assoc_gen,wcid;int func_tb_idx')
 text=text.replace('typedef struct {int MacTabLock;struct',
  'typedef struct {int MacTabLock;unsigned wr_iot_peer_delete_active,wr_assoc_event_users[8];struct wr_iot_peer_table_owner wr_iot_peer_table_owner;struct')
 text=text.replace('} AD,*PRTMP_ADAPTER;','} AD,*PRTMP_ADAPTER;\ntypedef AD RTMP_ADAPTER;typedef ENTRY MAC_TABLE_ENTRY;')
 return text
prefix=types(data['action_prefix'])
prefix=prefix.replace('unsigned Wcid;unsigned char Msg[256];','unsigned Wcid,assoc_gen,assoc_wcid;unsigned char assoc_addr[6],Msg[256];')
prefix=prefix.replace('fail_insert;','fail_insert,expect_scope=1;')
for actor in ('reqs','confirms'):
 prefix=prefix.replace(actor+'++;return MLME_SUCCESS;',
  'assert(!expect_scope||(ad->wr_assoc_event_users[e->wcid]==1&&ad->wr_iot_peer_table_owner.transactions==1));'+actor+'++;return MLME_SUCCESS;')
prefix=prefix.replace('.wcid=7,.client=1','.assoc_gen=1,.wcid=7,.client=1')
main=data['action_main'].replace('.MsgLen=38,.Wcid=7','.MsgLen=38,.Wcid=7,.assoc_gen=1,.assoc_wcid=7,.assoc_addr={42}')
main=main.replace('.wcid=7,.client=1','.assoc_gen=1,.wcid=7,.client=1')
main=main.replace('act->Action=FT_ACTION_BT_CONFIRM;FT_FtAction(&ad,&event);assert(confirms==1);',
 '''act->Action=FT_ACTION_BT_CONFIRM;right->assoc_gen=2;
 FT_FtAction(&ad,&event);assert(!confirms&&!ad.wr_assoc_event_users[7]&&!ad.wr_iot_peer_table_owner.transactions);
 right->assoc_gen=1;FT_FtAction(&ad,&event);assert(confirms==1);''')
main=main.replace('right->client=0;fail_insert=1;', 'event.assoc_gen=0;expect_scope=0;right->client=0;fail_insert=1;')
main=main.replace('assert(allocs==frees&&!ad.MacTabLock);',
 'assert(allocs==frees&&!ad.MacTabLock&&!ad.wr_assoc_event_users[7]&&!ad.wr_iot_peer_table_owner.transactions);')
consumer=prefix+'\n#include "ft-peer-generation.h"\n'+function('FT_FtAction')+main

prefix=types(data['base'])
prefix+='''
typedef unsigned char UCHAR;
#define NdisZeroMemory(a,n) memset(a,0,n)
#include "ft-peer-generation.h"
struct raw_rssi_info {unsigned char raw_rssi[3],raw_snr;};
static unsigned observed_gen;static int replace_on_alloc;
'''
actors=data['actors'].replace('allocated++;return 0;',
 'allocated++;if(replace_on_alloc){ad->MacTab.Content[7].assoc_gen++;replace_on_alloc=0;}return 0;')
enqueue=r'''
static int wr_ft_mlme_enqueue_for_recv(AD *ad,ULONG wcid,struct raw_rssi_info *rssi,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
 UCHAR snr0,UCHAR snr1,
#endif
 ULONG len,void *msg,UCHAR mode,const struct wr_ft_peer_stamp *expected){
 (void)ad;(void)rssi;(void)msg;(void)mode;
 observed_gen=expected->generation;enqueued++;queued_wcid=wcid;queued_length=len;return 1;
}
'''
main=data['main'].replace('.wcid=7,.func_tb_idx=2','.assoc_gen=1,.wcid=7,.func_tb_idx=2')
main=main.replace('assert(ad.MacTabLock==0);return 0;',r'''
 right->assoc_gen=5;replace_on_alloc=1;observed_gen=0;
 packet=calloc(1,38);assert(packet);packet[0]=2;r=(FT_RRB*)(packet+14);r->FTActLen=14;
 ((FT_ACTION*)r->Oct)->StaMac[0]=42;FT_RrbHandler(&ad,packet,38);free(packet);
 assert(observed_gen==5&&right->assoc_gen==6&&!replace_on_alloc);
 assert(ad.MacTabLock==0);return 0;
''')
producer=prefix+actors+enqueue+function('FT_RrbHandler')+main
with tempfile.TemporaryDirectory(prefix='wr-ft-generation-bind-') as td:
 for name,code in [('producer',producer),('consumer',consumer)]:
  src=Path(td)/(name+'.c');exe=Path(td)/name;src.write_text(code)
  for flags in ([],['-DCUSTOMER_DCC_FEATURE']):
   subprocess.run(['gcc','-std=gnu11','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),*flags,str(src),'-o',str(exe)],check=True)
   subprocess.run([str(exe)],check=True)
print('PASS | prepared FT snapshot binding | producer preserves pre-allocation generation; stale consumer refuses before insertion/handlers; balanced live peer scope; native zero-stamp path separate')
