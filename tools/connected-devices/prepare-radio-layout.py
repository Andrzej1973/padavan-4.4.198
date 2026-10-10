#!/usr/bin/env python3
"""Extract actual station types for target layout checks, without rate decoding."""
import argparse
import re
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('--output', required=True, type=Path)
a = p.parse_args()
code = '#include <stddef.h>\n#include <stdint.h>\ntypedef unsigned char UCHAR;\ntypedef signed char CHAR;\ntypedef uint32_t UINT32;\ntypedef unsigned short USHORT;\ntypedef unsigned long ULONG;\n#define MAC_ADDR_LEN 6\n#define ETHER_ADDR_LEN 6\n#define MAX_NUMBER_OF_MAC 64\n'
for name, path in [('shared', 'trunk/user/shared/include/ralink_priv.h')] + [(r, 'trunk/linux-4.4.x/drivers/net/wireless/mediatek/' + r + '/include/oid.h') for r in ('mt76x2', 'mt76x3')]:
    s = (a.source / path).read_text(encoding='utf-8')
    for kind, type_name, pointer in [('union', 'MACHTTRANSMIT_SETTING', 'PMACHTTRANSMIT_SETTING'), ('struct', 'RT_802_11_MAC_ENTRY', 'PRT_802_11_MAC_ENTRY'), ('struct', 'RT_802_11_MAC_TABLE', 'PRT_802_11_MAC_TABLE')]:
        match = re.search(r'typedef ' + kind + r' _' + type_name + r'\s*\{.*?' + pointer + ';', s, re.S)
        assert match, (name, type_name)
        text = match.group()
        for token in ('MACHTTRANSMIT_SETTING', 'PMACHTTRANSMIT_SETTING', '_MACHTTRANSMIT_SETTING', 'RT_802_11_MAC_ENTRY', 'PRT_802_11_MAC_ENTRY', '_RT_802_11_MAC_ENTRY', 'RT_802_11_MAC_TABLE', 'PRT_802_11_MAC_TABLE', '_RT_802_11_MAC_TABLE'):
            text = re.sub(r'\b' + token + r'\b', name + '_' + token, text)
        code += text + '\n'
    table = name + '_RT_802_11_MAC_TABLE'
    code += '_Static_assert(offsetof(' + table + ',Entry)==sizeof(unsigned long),"table header");\n'
    code += '_Static_assert(sizeof(' + table + ')==sizeof(unsigned long)+64*28,"64 client table");\n'
    t = name + '_RT_802_11_MAC_ENTRY'
    code += '_Static_assert(sizeof(' + t + ')==28,"entry size");\n'
    for field, offset in [('ApIdx',0), ('Addr',1), ('AvgRssi0',10), ('AvgRssi1',11), ('AvgRssi2',12), ('ConnectedTime',16), ('TxRate',20), ('LastRxRate',24)]:
        code += '_Static_assert(offsetof(' + t + ',' + field + ')==' + str(offset) + ',"' + field + '");\n'
code += '#include <assert.h>\n#define RT_802_11_MAC_TABLE shared_RT_802_11_MAC_TABLE\n#define RT_802_11_MAC_ENTRY shared_RT_802_11_MAC_ENTRY\n'
code += '#include "' + str(Path(__file__).resolve().parent / 'radio-table.h').replace('\\', '/') + '"\n'
code += '#define RTPRIV_IOCTL_GET_MAC_TABLE_STRUCT (SIOCIWFIRSTPRIV + 0x1F)\n'
code += '#include "' + str(Path(__file__).resolve().parent / 'radio-query.h').replace('\\', '/') + '"\n'
code += '#include "' + str(Path(__file__).resolve().parent / 'radio-merge.h').replace('\\', '/') + '"\n'
code += r"""
static int mock_query(const char *interface, int command, struct iwreq *request, void *context) {
 int mode=*(int *)context;
 RT_802_11_MAC_TABLE *table=request->u.data.pointer;
 assert(!strcmp(interface,"ra0"));
 assert(command==RTPRIV_IOCTL_GET_MAC_TABLE_STRUCT);
 assert(request->u.data.length==sizeof(*table) && table->Num==ULONG_MAX);
 if(mode==1) return -1;
 if(mode==2) return 0;
 table->Num=0;
 if(mode==3) request->u.data.length=0;
 return 0;
}
int main(void) {
 RT_802_11_MAC_TABLE table;
 struct wr_radio_snapshot output, before;
 memset(&output, 0x55, sizeof(output)); before=output;
 wr_radio_prepare(&table);
 assert(!wr_radio_decode(&table,sizeof(table),2,&output));
 assert(!memcmp(&output,&before,sizeof(output)));
 table.Num=0;
 assert(wr_radio_decode(&table,sizeof(table),2,&output) && output.count==0);
 table.Num=1; table.Entry[0].Addr[0]=2; table.Entry[0].Addr[5]=1;
 table.Entry[0].AvgRssi0=-70; table.Entry[0].AvgRssi1=-50;
 table.Entry[0].ApIdx=2;
 assert(wr_radio_decode(&table,sizeof(table),2,&output));
 assert(output.count==1 && output.clients[0].rssi==-50 && output.clients[0].ap_index==2);
 before=output;
 assert(!wr_radio_decode(&table,sizeof(table)-1,2,&output));
 table.Num=65; assert(!wr_radio_decode(&table,sizeof(table),2,&output));
 table.Num=2; table.Entry[1]=table.Entry[0];
 assert(!wr_radio_decode(&table,sizeof(table),2,&output));
 assert(!memcmp(&output,&before,sizeof(output)));
 table.Num=1; table.Entry[0].AvgRssi0=1;
 assert(!wr_radio_decode(&table,sizeof(table),2,&output));
 {
  int mode;
  before=output;
  for(mode=1;mode<=3;mode++) {
   assert(!wr_radio_query("ra0",2,mock_query,&mode,&output));
   assert(!memcmp(&before,&output,sizeof(output)));
  }
  mode=0;
  assert(wr_radio_query("ra0",2,mock_query,&mode,&output) && output.count==0);
 }
 {
  struct wr_device_snapshot base;
  struct wr_radio_snapshot two, five;
  static struct wr_device_joined_snapshot joined;
  memset(&base,0,sizeof(base)); memset(&two,0,sizeof(two)); memset(&five,0,sizeof(five));
  base.count=1; strcpy(base.records[0].mac,"02:00:00:00:00:01"); strcpy(base.records[0].name,"known");
  two.count=1; two.clients[0].mac[0]=2; two.clients[0].mac[5]=1; two.clients[0].rssi=-60;
  five=two; five.clients[0].rssi=-45;
  assert(wr_device_radio_merge(&base,&two,&five,&joined));
  assert(joined.networkmap.count==1 && joined.networkmap.records[0].radio.band_mask==3 && joined.networkmap.records[0].radio.rssi[1]==-45);
  five.clients[0].mac[5]=2;
  assert(wr_device_radio_merge(&base,&two,&five,&joined));
  assert(joined.networkmap.count==2 && joined.networkmap.records[1].ip[0]==0);
  assert(joined.networkmap.records[1].radio.band_mask==2 && !strcmp(joined.networkmap.records[0].name,"known"));
  base.count=128;
  assert(wr_device_radio_merge(&base,&two,&five,&joined));
  assert(joined.networkmap.count==128 && joined.networkmap.truncated);
 }
 return 0;
}
"""
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(code, encoding='utf-8')
print('Generated actual station-type layout assertions; compile with the target compiler')
