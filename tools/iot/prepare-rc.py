#!/usr/bin/env python3
"""Install WR-only bridge object and owned IoT quiescence before radio shutdown."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
rc=a.source/'trunk/user/rc';local=Path(__file__).parent
board=a.source/'trunk/configs/boards/WR1200JS/l1profile.dat'
s=board.read_text(encoding='utf-8')
if 'INDEX0_main_ifname=ra0' not in s or 'INDEX0_ext_ifname=ra\n' not in s:raise SystemExit('WR1200JS third BSS interface assumptions changed')
f=rc/'net_wifi.c';s=f.read_text(encoding='utf-8')
anchor='void \nstop_wifi_all_rt(void)\n{'
if s.count(anchor)!=1 or 'wr_iot_quiesce' in s:raise SystemExit('Wi-Fi stop anchor changed or already prepared')
helper="""#if defined(BOARD_WR1200JS)
#include "wr-iot/bridge.h"
static void wr_iot_quiesce(void)
{
 if (!wr_iot_bridge_is_owned()) return;
 wif_control("ra2", 0);
 if (!wr_iot_bridge_detach())
  logmessage("IoT Wi-Fi", "Interface stop not confirmed; isolation must be retained");
}
#endif

"""
s=s.replace(anchor,helper+anchor+'\n#if defined(BOARD_WR1200JS)\n wr_iot_quiesce();\n#endif',1)
m=rc/'Makefile';make=m.read_text(encoding='utf-8');anchor='OBJS += gpio_btn.o btn_action.o'
if make.count(anchor)!=1:raise SystemExit('RC object anchor changed')
make=make.replace(anchor,anchor+'\nifneq ($(findstring -DBOARD_WR1200JS,$(CFLAGS)),)\nOBJS += wr-iot-bridge.o\nendif',1)
headers=rc/'wr-iot';headers.mkdir(exist_ok=True)
for name in ('bridge.h','subnet.h','types.h'):(headers/name).write_bytes((local/name).read_bytes())
bridge=(local/'bridge.c').read_text(encoding='utf-8').replace('#include "bridge.h"','#include "wr-iot/bridge.h"',1).replace('#include "subnet.h"','#include "wr-iot/subnet.h"',1)
(rc/'wr-iot-bridge.c').write_text(bridge,encoding='utf-8');f.write_text(s,encoding='utf-8');m.write_text(make,encoding='utf-8')
report={'board':'WR1200JS','candidate_bss':'ra2','bridge_object_installed':True,'owned_quiescence_before_radio_stop':True,'activation_integrated':False,'runtime_verified':False}
(a.source/'iot-rc-source.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS WR-only IoT bridge object and owned quiescence source integration; activation pending')
