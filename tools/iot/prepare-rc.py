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
 if (nvram_get_int("wr_iot_network_t"))
  nvram_set_int_temp("wr_iot_network_t", 0);
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
coordinated='#ifdef USE_WR_BAND_STEERING_PROFILE\n\t{\n\t\tint failed = ferror(fp);'
if radio.count(coordinated)==1:anchor=coordinated
elif radio.count(anchor)!=1:raise SystemExit('Profile completion anchor changed')
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
# Only a future validated network snapshot may activate this service fragment.
f=rc/'services_ex.c';service=f.read_text(encoding='utf-8')
anchor='int\nstart_dns_dhcpd(int is_ap_mode)'
if service.count(anchor)!=1:raise SystemExit('DHCP service anchor changed')
helper=r"""#if defined(BOARD_WR1200JS)
#include "wr-iot/dhcp-write.h"
#include "wr-iot/network-check.h"
#include "wr-iot/service-state.h"
static int wr_iot_dnsmasq(FILE *fp,int is_ap_mode,const char *lan_ip,const char *lan_mask)
{
 const char *keys[]={"wr_iot_gateway_t","wr_iot_mask_t","wr_iot_start_t","wr_iot_end_t"};
 char values[4][16];const char *value;size_t i,n;
 if (nvram_get_int("wr_iot_network_t") != 1) return 0;
 for (i=0;i<4;i++) {
  value=nvram_safe_get(keys[i]);n=strlen(value);
  if (n>=sizeof(values[i])) return -1;
  memcpy(values[i],value,n+1);
 }
 if (is_ap_mode || !wr_iot_network_check(values[0],values[1],values[2],values[3])) return -1;
 return wr_iot_dhcp_write(fp,!is_ap_mode,values[0],values[1],values[2],values[3],lan_ip,lan_mask)?1:-1;
}
#endif

"""
service=service.replace(anchor,helper+anchor,1)
anchor='\tif (is_dhcp_used & 0x1) {'
if service.count(anchor)!=1:raise SystemExit('DHCP lease configuration anchor changed')
hook=r"""#if defined(BOARD_WR1200JS)
 {
  int result=wr_iot_dnsmasq(fp,is_ap_mode,ipaddr,netmask);
  if (result<0) {fclose(fp);return EINVAL;}
  if (result>0) is_dhcp_used |= 0x1;
 }
#endif

"""
service=service.replace(anchor,hook+anchor,1)
for name in ('dhcp-write.h','dhcp.h'):(headers/name).write_bytes((local/name).read_bytes())
writer=(local/'dhcp-write.c').read_text(encoding='utf-8').replace('#include "dhcp-write.h"','#include "wr-iot/dhcp-write.h"').replace('#include "dhcp.h"','#include "wr-iot/dhcp.h"')
(rc/'wr-iot-dhcp.c').write_text(writer,encoding='utf-8')
m.write_text(m.read_text(encoding='utf-8').replace('wr-iot-bridge.o wr-iot-profile.o','wr-iot-bridge.o wr-iot-profile.o wr-iot-dhcp.o'),encoding='utf-8')
f.write_text(service,encoding='utf-8')
report['dhcp_hook_installed']=True
report['network_activation_guard']='wr_iot_network_t; no startup sets this state yet; full route/VPN validation still required'
for name in ('network-check.h','inventory.h','route-prefix.h','route-snapshot.h'):
 (headers/name).write_bytes((local/name).read_bytes())
network=(local/'network-check.c').read_text(encoding='utf-8')
for name in ('network-check.h','bridge.h','route-snapshot.h','subnet.h'):
 network=network.replace('#include "'+name+'"','#include "wr-iot/'+name+'"')
(rc/'wr-iot-network.c').write_text(network,encoding='utf-8')
m.write_text(m.read_text(encoding='utf-8').replace('wr-iot-dhcp.o','wr-iot-dhcp.o wr-iot-network.o'),encoding='utf-8')
report['dhcp_network_inventory_check']=True
report['network_activation_guard']='wr_iot_network_t; interface and all-table route precheck installed; serialization and startup still pending'
# Stage the main config only for the internal IoT gate; legacy OFF path is retained.
service=f.read_text(encoding='utf-8')
begin=service.index('int\nstart_dns_dhcpd(int is_ap_mode)')
end=service.index('\nvoid\nstop_dns_dhcpd(void)',begin)
part=service[begin:end]
anchor='\t/* touch dnsmasq.leases if not exist */'
if part.count(anchor)!=1:raise SystemExit('DHCP early preflight anchor changed')
early=r"""#if defined(BOARD_WR1200JS)
 if(nvram_get_int("wr_iot_network_t") == 1) {
  FILE *scratch=tmpfile();int checked,failed;
  if(!scratch)return errno;
  checked=wr_iot_dnsmasq(scratch,is_ap_mode,ipaddr,netmask);
  failed=ferror(scratch);if(fclose(scratch))failed=1;
  if(checked!=1||failed)return EINVAL;
 }
#endif
"""
part=part.replace(anchor,early+anchor,1)
anchor='\tFILE *fp;'
if part.count(anchor)!=1:raise SystemExit('DHCP staging local anchor changed')
part=part.replace(anchor,anchor+'\n#if defined(BOARD_WR1200JS)\n char iot_candidate[32]="";\n#endif',1)
anchor='\tif (!(fp = fopen("/etc/dnsmasq.conf", "w")))\n\t\treturn errno;'
if part.count(anchor)!=1:raise SystemExit('DHCP config open anchor changed')
opening=r"""#if defined(BOARD_WR1200JS)
 if (nvram_get_int("wr_iot_network_t") == 1) {
  int fd,saved;
  strcpy(iot_candidate,"/etc/dnsmasq.iot.XXXXXX");
  fd=mkstemp(iot_candidate);if(fd<0)return errno;
  fp=fdopen(fd,"w");
  if(!fp){saved=errno;close(fd);unlink(iot_candidate);return saved;}
 } else
#endif
"""
part=part.replace(anchor,opening+anchor,1)
anchor='if (result<0) {fclose(fp);return EINVAL;}'
if part.count(anchor)!=1:raise SystemExit('DHCP candidate rejection anchor changed')
part=part.replace(anchor,'if (result<0) {fclose(fp);if(*iot_candidate)unlink(iot_candidate);return EINVAL;}',1)
anchor='\tfclose(fp);\n\tif (is_dns_used)'
if part.count(anchor)!=1:raise SystemExit('DHCP staged close anchor changed')
closing=r"""#if defined(BOARD_WR1200JS)
 if(*iot_candidate) {
  int failed=ferror(fp);
  if(fflush(fp)||fsync(fileno(fp)))failed=1;
  if(fclose(fp))failed=1;
  if(failed){unlink(iot_candidate);return EIO;}
 } else
#endif
"""
part=part.replace(anchor,closing+anchor,1)
anchor='\tif (is_dns_used || is_dhcp_used)'
if part.count(anchor)!=1:raise SystemExit('DHCP candidate parse anchor changed')
commit=r"""#if defined(BOARD_WR1200JS)
 if(*iot_candidate) {
  char option[64];int saved;
  snprintf(option,sizeof(option),"--conf-file=%s",iot_candidate);
  if(eval("/usr/sbin/dnsmasq","--test",option)){unlink(iot_candidate);return EINVAL;}
  if(rename(iot_candidate,"/etc/dnsmasq.conf")){saved=errno;unlink(iot_candidate);return saved;}
 }
#endif
"""
part=part.replace(anchor,commit+anchor,1)
service=service[:begin]+part+service[end:]
# Serialize these entry points only while the internal IoT network gate is set.
# Other hosts/resolv writers and a complete restart rollback still need integration.
service=service.replace('int\nstart_dns_dhcpd(int is_ap_mode)', 'static int\nwr_iot_start_dns_raw(int is_ap_mode)',1)
service=service.replace('void\nstop_dns_dhcpd(void)', 'static void\nwr_iot_stop_dns_raw(void)',1)
anchor='int\nrestart_dhcpd(void)\n{\n\tstop_dns_dhcpd();\n\treturn start_dns_dhcpd(get_ap_mode());\n}'
if service.count(anchor)!=1:raise SystemExit('DNS restart serialization anchor changed')
wrappers=r"""#if defined(BOARD_WR1200JS)
static int wr_iot_dns_lock(struct wr_iot_service_lock *lock)
{
 if(nvram_get_int("wr_iot_network_t")!=1)return 1;
 if(wr_iot_service_lock_take(lock,"/var/run/wr-iot-services.lock"))return 1;
 logmessage("IoT Wi-Fi","DNS/DHCP transaction busy; service operation deferred");
 return 0;
}
#endif
int
start_dns_dhcpd(int is_ap_mode)
{
#if defined(BOARD_WR1200JS)
 struct wr_iot_service_lock lock={-1};int result;
 if(!wr_iot_dns_lock(&lock))return EBUSY;
 result=wr_iot_start_dns_raw(is_ap_mode);wr_iot_service_lock_release(&lock);return result;
#else
 return wr_iot_start_dns_raw(is_ap_mode);
#endif
}
void
stop_dns_dhcpd(void)
{
#if defined(BOARD_WR1200JS)
 struct wr_iot_service_lock lock={-1};
 if(!wr_iot_dns_lock(&lock))return;
 wr_iot_stop_dns_raw();wr_iot_service_lock_release(&lock);
#else
 wr_iot_stop_dns_raw();
#endif
}
int
restart_dhcpd(void)
{
#if defined(BOARD_WR1200JS)
 struct wr_iot_service_lock lock={-1};int result;
 if(!wr_iot_dns_lock(&lock))return EBUSY;
 wr_iot_stop_dns_raw();result=wr_iot_start_dns_raw(get_ap_mode());
 wr_iot_service_lock_release(&lock);return result;
#else
 wr_iot_stop_dns_raw();return wr_iot_start_dns_raw(get_ap_mode());
#endif
}
"""
service=service.replace(anchor,wrappers,1)
f.write_text(service,encoding='utf-8')
report['dnsmasq_entry_points_serialized_when_iot_gated']=True
report['all_dnsmasq_writers_serialized']=False
for name in ('service-state.h','service-transaction.h','service-lock.h','dnsmasq-files.h','saved-bundle.h','saved-file.h','restore-file.h','uts-state.h','arp-state.h','arp-restore.h'):
 (headers/name).write_bytes((local/name).read_bytes())
report['service_state_headers_installed']=True
report['service_state_lifecycle_bound']=False
report['iot_main_dnsmasq_config_staged']=True
report['dnsmasq_service_rollback_complete']=False
(a.source/'iot-rc-source.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS WR-only IoT bridge object and owned quiescence source integration; activation pending')
