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
 if (nvram_get_int("wr_iot_profile_t"))
  nvram_set_int_temp("wr_iot_profile_t", 0);
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
# Profile activation remains gated by an internal temporary preparation state.
f=rc/'ralink.c';radio=f.read_text(encoding='utf-8')
anchor='\tfclose(fp);\n\n\treturn 0;\n}\n\nint\ngen_ralink_config_2g'
if radio.count(anchor)!=1:raise SystemExit('Profile completion anchor changed')
radio=radio.replace('static int\ngen_ralink_config(', '#if defined(BOARD_WR1200JS)\n#include "wr-iot/profile.h"\n#endif\n\nstatic int\ngen_ralink_config(',1)
hook=r"""#if defined(BOARD_WR1200JS)
 if (!is_aband && nvram_get_int("wr_iot_profile_t") == 1) {
  char ssid[33],password[65];const char *value;size_t n;int failed=ferror(fp);
  if (fclose(fp)) failed=1;
  if (failed || !is_soc_ap || get_ap_mode() || i_mode_x==1 || i_mode_x==3) return -1;
  value=nvram_safe_get("wr_iot_ssid");n=strlen(value);
  if (n>=sizeof(ssid)) return -1;
  memcpy(ssid,value,n+1);
  value=nvram_safe_get("wr_iot_psk");n=strlen(value);
  if (n>=sizeof(password)) return -1;
  memcpy(password,value,n+1);
  return wr_iot_profile_apply(dat_file,ssid,password)?0:-1;
 }
#endif
"""
radio=radio.replace(anchor,hook+anchor,1)
for name in ('profile.h','profile-list.h','profile-line.h','profile-stream.h','profile-file.h'):
 (headers/name).write_bytes((local/name).read_bytes())
shared=rc/'shared-wifi';shared.mkdir(exist_ok=True)
(shared/'validate.h').write_bytes((local.parent/'shared-wifi/validate.h').read_bytes())
profile=(local/'profile.c').read_text(encoding='utf-8').replace('#include "profile.h"','#include "wr-iot/profile.h"').replace('#include "profile-file.h"','#include "wr-iot/profile-file.h"')
(rc/'wr-iot-profile.c').write_text(profile,encoding='utf-8')
m.write_text(m.read_text(encoding='utf-8').replace('OBJS += wr-iot-bridge.o','OBJS += wr-iot-bridge.o wr-iot-profile.o'),encoding='utf-8')
f.write_text(radio,encoding='utf-8')
report['profile_hook_installed']=True
report['profile_activation_guard']='wr_iot_profile_t; no startup sets this state yet'
(a.source/'iot-rc-source.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS WR-only IoT bridge object and owned quiescence source integration; activation pending')
