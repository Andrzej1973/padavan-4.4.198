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
 if (!wr_iot_bridge_set_up(0) || !wr_iot_bridge_detach())
  logmessage("IoT Wi-Fi", "Interface/bridge stop not confirmed; isolation must be retained");
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
#include "wr-iot/service-guard.h"
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
  if(!wr_iot_writer_journal_begin(1U)){unlink(iot_candidate);return EIO;}
  if(rename(iot_candidate,"/etc/dnsmasq.conf")){
   saved=errno;(void)wr_iot_writer_journal_end(1U);unlink(iot_candidate);return saved;
  }
  if(!wr_iot_writer_journal_end(1U))return EIO;
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
controller=(local/"restart-controller.inc").read_text(encoding="utf-8").replace('#include "dns-ready.h"','#include "wr-iot/dns-ready.h"').replace('#include "dns-config.h"','#include "wr-iot/dns-config.h"').replace('#include "dhcp-ready.h"','#include "wr-iot/dhcp-ready.h"').replace('#include "dns-sockets.h"','#include "wr-iot/dns-sockets.h"')
for name in ("dns-ready.h","dns-config.h","dhcp-ready.h","dns-sockets.h"):(headers/name).write_bytes((local/name).read_bytes())
wrappers=r"""#if defined(BOARD_WR1200JS)
static int wr_iot_dns_lock(void)
{
 int token=wr_iot_service_guard_enter(nvram_get_int("wr_iot_network_t")==1);
 if(token)return token;
 logmessage("IoT Wi-Fi","DNS/DHCP transaction busy; service operation deferred");
 return 0;
}
#endif
int
start_dns_dhcpd(int is_ap_mode)
{
#if defined(BOARD_WR1200JS)
 int token=wr_iot_dns_lock(),result;
 if(!token)return EBUSY;
 result=wr_iot_start_dns_raw(is_ap_mode);wr_iot_service_guard_leave(token);return result;
#else
 return wr_iot_start_dns_raw(is_ap_mode);
#endif
}
void
stop_dns_dhcpd(void)
{
#if defined(BOARD_WR1200JS)
 int token=wr_iot_dns_lock();
 if(!token)return;
 wr_iot_stop_dns_raw();wr_iot_service_guard_leave(token);
#else
 wr_iot_stop_dns_raw();
#endif
}
int
restart_dhcpd(void)
{
#if defined(BOARD_WR1200JS)
 int token=wr_iot_dns_lock(),result;
 if(!token)return EBUSY;
 if(wr_iot_restart_active){result=wr_iot_restart_transaction();wr_iot_service_guard_leave(token);return result;}
 if(nvram_get_int("wr_iot_network_t")==1){
  FILE *scratch=tmpfile();int checked,failed;
  if(!scratch){result=errno;wr_iot_service_guard_leave(token);return result;}
  checked=wr_iot_dnsmasq(scratch,get_ap_mode(),nvram_safe_get("lan_ipaddr"),nvram_safe_get("lan_netmask"));
  failed=ferror(scratch);if(fclose(scratch))failed=1;
  if(checked!=1||failed){wr_iot_service_guard_leave(token);return EINVAL;}
 }
 if(nvram_get_int("wr_iot_network_t")==1)result=wr_iot_restart_transaction();
 else {wr_iot_stop_dns_raw();result=wr_iot_start_dns_raw(get_ap_mode());}
 wr_iot_service_guard_leave(token);return result;
#else
 wr_iot_stop_dns_raw();return wr_iot_start_dns_raw(get_ap_mode());
#endif
}
"""
service=service.replace(anchor,controller+wrappers,1)
f.write_text(service,encoding='utf-8')
report['dnsmasq_entry_points_serialized_when_iot_gated']=True
report['all_dnsmasq_writers_serialized']=False
# These public writers are also called outside start_dns_dhcpd.
def guarded_writer(text,name,args,call):
 signature='int\n'+name+'('+args+')\n{'
 if text.count(signature)!=1:raise SystemExit('DNS writer anchor changed: '+name)
 begin=text.index(signature);end=text.index('\n}\n',begin)+3
 raw=text[begin:end].replace(signature,'static int\nwr_iot_'+name+'_raw('+args+')\n{',1)
 wrapper='\n/* WR_IOT_WRITE_WRAPPER_START '+name+' */\n#if defined(BOARD_WR1200JS)\n#include "wr-iot/service-guard.h"\n#endif\nint\n'+name+'('+args+')\n{\n#if defined(BOARD_WR1200JS)\n int token=wr_iot_service_guard_enter(nvram_get_int("wr_iot_network_t")==1),result;\n if(!token)return EBUSY;\n result=wr_iot_'+name+'_raw('+call+');wr_iot_service_guard_leave(token);return result;\n#else\n return wr_iot_'+name+'_raw('+call+');\n#endif\n}\n/* WR_IOT_WRITE_WRAPPER_END '+name+' */\n'
 return text[:begin]+raw+wrapper+text[end:]
service=guarded_writer(service,'fill_dnsmasq_servers','void','')
f.write_text(service,encoding='utf-8')
wan=rc/'net_wan.c';text=wan.read_text(encoding='utf-8')
text=guarded_writer(text,'update_resolvconf','int is_first_run, int do_not_notify','is_first_run,do_not_notify')
text=guarded_writer(text,'update_hosts_router','const char *lan_ipaddr','lan_ipaddr')
wan.write_text(text,encoding='utf-8')
report['wan_resolv_hosts_and_dnsmasq_servers_serialized_when_iot_gated']=True
def guarded_lan_writer(text,name,args,call):
 prefix='void' if name=='lan_up_manual' else 'static void'
 signature=prefix+'\n'+name+'('+args+')\n{'
 if text.count(signature)!=1:raise SystemExit('LAN DNS writer anchor changed: '+name)
 begin=text.index(signature);end=text.index('\n}\n',begin)+3
 raw=text[begin:end].replace(signature,'static void\nwr_iot_'+name+'_raw('+args+')\n{',1)
 wrapper='\n/* WR_IOT_LAN_WRAPPER_START '+name+' */\n#if defined(BOARD_WR1200JS)\n#include "wr-iot/service-guard.h"\n#endif\n'+prefix+'\n'+name+'('+args+')\n{\n#if defined(BOARD_WR1200JS)\n int token=wr_iot_service_guard_enter(nvram_get_int("wr_iot_network_t")==1);\n if(!token){logmessage("IoT Wi-Fi","LAN DNS transaction busy; operation skipped");return;}\n wr_iot_'+name+'_raw('+call+');wr_iot_service_guard_leave(token);\n#else\n wr_iot_'+name+'_raw('+call+');\n#endif\n}\n/* WR_IOT_LAN_WRAPPER_END '+name+' */\n'
 return text[:begin]+raw+wrapper+text[end:]
lan=rc/'net_lan.c';text=lan.read_text(encoding='utf-8')
for name,args,call in [('lan_up_manual','char *lan_ifname, char *lan_dname','lan_ifname,lan_dname'),('lan_up_auto','char *lan_ifname, char *lan_gateway, char *lan_dname','lan_ifname,lan_gateway,lan_dname'),('lan_down_auto','char *lan_ifname','lan_ifname')]:
 text=guarded_lan_writer(text,name,args,call)
lan.write_text(text,encoding='utf-8')
report['lan_resolv_writer_callbacks_serialized_when_iot_gated']=True
def guarded_sequence(text,name,args,call,signature):
 if text.count(signature)!=1:raise SystemExit('Service sequence anchor changed: '+name)
 begin=text.index(signature);end=text.index('\n}\n',begin)+3
 raw=text[begin:end].replace(signature,'static void\nwr_iot_'+name+'_raw('+args+')\n{',1)
 wrapper='\n/* WR_IOT_SEQUENCE_START '+name+' */\n#if defined(BOARD_WR1200JS)\n#include "wr-iot/service-guard.h"\n#endif\nvoid\n'+name+'('+args+')\n{\n#if defined(BOARD_WR1200JS)\n int token=wr_iot_service_guard_enter(nvram_get_int("wr_iot_network_t")==1);\n if(!token){logmessage("IoT Wi-Fi","Service transaction busy; restart skipped");return;}\n wr_iot_'+name+'_raw('+call+');wr_iot_service_guard_leave(token);\n#else\n wr_iot_'+name+'_raw('+call+');\n#endif\n}\n/* WR_IOT_SEQUENCE_END '+name+' */\n'
 return text[:begin]+raw+wrapper+text[end:]
text=guarded_sequence(text,'full_restart_lan','void','','void \nfull_restart_lan(void)\n{')
lan.write_text(text,encoding='utf-8')
ipv6=rc/'net6.c';six=ipv6.read_text(encoding='utf-8')
six=guarded_sequence(six,'full_restart_ipv6','int ipv6_type_old','ipv6_type_old','void full_restart_ipv6(int ipv6_type_old)\n{')
ipv6.write_text(six,encoding='utf-8')
report['lan_ipv6_full_restart_sequences_serialized_when_iot_gated']=True



# Instrument actual writer bodies, including early returns and failed writes.
# No lifecycle controller binds a journal yet; unbound operation stays unchanged.
def journal_writer(text,name,args,call,mask,returns_int=True,kernel=False):
 prefix='static int' if returns_int else 'static void'
 signature=prefix+'\n'+name+'('+args+')\n{'
 if text.count(signature)!=1:raise SystemExit('Journal writer anchor changed: '+name)
 begin=text.index(signature);end=text.index('\n}\n',begin)+3
 body=text[begin:end].replace(signature,prefix+'\n'+name+'_owned_body('+args+')\n{',1)
 refusal='return EIO;' if returns_int else 'return;'
 invoke=('int result='+name+'_owned_body('+call+');' if returns_int else name+'_owned_body('+call+');')
 finish=('if(!wr_iot_writer_journal_end('+str(mask)+'U))return EIO;return result;' if returns_int else '(void)wr_iot_writer_journal_end('+str(mask)+'U);')
 kernel_begin=('if(!wr_iot_writer_journal_kernel_begin()){(void)wr_iot_writer_journal_end('+str(mask)+'U);'+refusal+'}\n' if kernel else '')
 kernel_end=('int kernel_ok=wr_iot_writer_journal_kernel_end();' if returns_int else '(void)wr_iot_writer_journal_kernel_end();') if kernel else ''
 if kernel and returns_int:finish=finish.replace('return result;','return kernel_ok?result:EIO;')
 wrapper='\n'+prefix+'\n'+name+'('+args+')\n{\n#if defined(BOARD_WR1200JS)\n if(!wr_iot_writer_journal_begin('+str(mask)+'U)){'+refusal+'}\n '+kernel_begin+' { '+invoke+kernel_end+finish+' }\n#else\n '+('return ' if returns_int else '')+name+'_owned_body('+call+');\n#endif\n}\n'
 return text[:begin]+body+wrapper+text[end:]
for filename,entries in [
 ('services_ex.c',[('fill_static_ethers','const char *lan_ip, const char *lan_mask','lan_ip,lan_mask',14,False,True),('wr_iot_fill_dnsmasq_servers_raw','void','',64,True)]),
 ('net_wan.c',[('wr_iot_update_resolvconf_raw','int is_first_run, int do_not_notify','is_first_run,do_not_notify',128,True),('wr_iot_update_hosts_router_raw','const char *lan_ipaddr','lan_ipaddr',48,True,True)]),
 ('net_lan.c',[('wr_iot_lan_up_manual_raw','char *lan_ifname, char *lan_dname','lan_ifname,lan_dname',128,False),('wr_iot_lan_up_auto_raw','char *lan_ifname, char *lan_gateway, char *lan_dname','lan_ifname,lan_gateway,lan_dname',128,False),('wr_iot_lan_down_auto_raw','char *lan_ifname','lan_ifname',128,False)])]:
 path=rc/filename;source=path.read_text(encoding='utf-8')
 source=source.replace('#include "rc.h"','#include "rc.h"\n#if defined(BOARD_WR1200JS)\n#include "wr-iot/writer-journal.h"\n#endif',1)
 for entry in entries:source=journal_writer(source,*entry)
 path.write_text(source,encoding='utf-8')
# Propagate journal failures from legacy void helpers before starting a daemon.
path=rc/'services_ex.c';source=path.read_text(encoding='utf-8')
for call in ['fill_static_ethers(ipaddr, netmask);','update_hosts_router(ipaddr);']:
 if source.count(call)!=1:raise SystemExit('DNS startup helper anchor changed: '+call)
 source=source.replace(call,call+'\n#if defined(BOARD_WR1200JS)\n if(wr_iot_writer_journal_failed())return EIO;\n#endif',1)
anchor='create_file(DNS_RESOLV_CONF);'
if source.count(anchor)!=1:raise SystemExit('DNS resolver touch anchor changed')
source=source.replace(anchor,"""#if defined(BOARD_WR1200JS)
        if(!wr_iot_writer_journal_begin(128U))return EIO;
#endif
        create_file(DNS_RESOLV_CONF);
#if defined(BOARD_WR1200JS)
        if(!wr_iot_writer_journal_end(128U))return EIO;
#endif""",1)
path.write_text(source,encoding='utf-8')
report['startup_auxiliary_journal_failure_propagated']=True
# Stop-side permanent ARP clear is a kernel writer too.
path=rc/'services_ex.c';source=path.read_text(encoding='utf-8')
signature='static void\narpbind_clear(void)\n{'
if source.count(signature)!=1:raise SystemExit('ARP clear writer anchor changed')
begin=source.index(signature);end=source.index('\n}\n',begin)+3
body=source[begin:end].replace('arpbind_clear(void)','wr_iot_arpbind_clear_body(void)',1)
wrapper="""
static void
arpbind_clear(void)
{
#if defined(BOARD_WR1200JS)
 if(!wr_iot_writer_journal_kernel_begin())return;
#endif
 wr_iot_arpbind_clear_body();
#if defined(BOARD_WR1200JS)
 (void)wr_iot_writer_journal_kernel_end();
#endif
}
"""
source=source[:begin]+body+wrapper+source[end:];path.write_text(source,encoding='utf-8')
# Capture real stdio failures within owned auxiliary writer bodies.
for filename,names in [('services_ex.c',['fill_static_ethers_owned_body','wr_iot_fill_dnsmasq_servers_raw_owned_body']),('net_wan.c',['wr_iot_update_hosts_router_raw_owned_body','wr_iot_update_resolvconf_raw_owned_body'])]:
 path=rc/filename;source=path.read_text(encoding='utf-8')
 source=source.replace('#include "rc.h"',"""#include "rc.h"
#if defined(BOARD_WR1200JS)
#define WR_IOT_FOPEN wr_iot_writer_fopen
#define WR_IOT_FCLOSE wr_iot_writer_fclose
#else
#define WR_IOT_FOPEN fopen
#define WR_IOT_FCLOSE fclose
#endif""",1)
 for name in names:
  start=source.index('\n'+name+'(');end=source.index('\n}\n',start)+3
  body=source[start:end].replace('fopen(','WR_IOT_FOPEN(').replace('fclose(','WR_IOT_FCLOSE(')
  source=source[:start]+body+source[end:]
 if filename=='services_ex.c':
  anchor='\tif (is_dns_used)\n\t\tfill_dnsmasq_servers();'
  if source.count(anchor)!=1:raise SystemExit('DNS servers startup anchor changed')
  source=source.replace(anchor,anchor+'\n#if defined(BOARD_WR1200JS)\n if(wr_iot_writer_journal_failed()){if(*iot_candidate)unlink(iot_candidate);return EIO;}\n#endif',1)
 path.write_text(source,encoding='utf-8')
path=rc/'net_wan.c';source=path.read_text(encoding='utf-8')
for call in ['sethostname(lan_hname, strlen(lan_hname))','setdomainname(lan_dname, strlen(lan_dname))']:
 anchor='\t'+call+';'
 if source.count(anchor)!=1:raise SystemExit('UTS setter anchor changed: '+call)
 source=source.replace(anchor,'#if defined(BOARD_WR1200JS)\n if('+call+')wr_iot_writer_journal_error();\n#else\n'+anchor+'\n#endif',1)
path.write_text(source,encoding='utf-8')
report['uts_setter_errors_latched']=True
report['owned_auxiliary_stdio_failures_latched']=True
report['uts_and_permanent_arp_writer_bodies_instrumented']=True
report['auxiliary_dns_writer_bodies_journal_instrumented']=True
report['writer_journal_lifecycle_bound']=False
(headers/'writer-journal.h').write_bytes((local/'writer-journal.h').read_bytes())
(rc/'wr-iot-writer-journal.c').write_text((local/'writer-journal.c').read_text(encoding='utf-8').replace('#include "writer-journal.h"','#include "wr-iot/writer-journal.h"').replace('#include "service-state.h"','#include "wr-iot/service-state.h"'),encoding='utf-8')
m.write_text(m.read_text(encoding='utf-8').replace('OBJS += wr-iot-bridge.o','OBJS += wr-iot-writer-journal.o wr-iot-bridge.o'),encoding='utf-8')

for name in ('service-state.h','service-transaction.h','service-lock.h','dnsmasq-files.h','saved-bundle.h','saved-file.h','restore-file.h','uts-state.h','arp-state.h','arp-restore.h'):
 (headers/name).write_bytes((local/name).read_bytes())
(headers/'service-guard.h').write_bytes((local/'service-guard.h').read_bytes())
(rc/'wr-iot-service-guard.c').write_text((local/'service-guard.c').read_text(encoding='utf-8').replace('#include \"service-lock.h\"','#include \"wr-iot/service-lock.h\"').replace('#include \"service-guard.h\"','#include \"wr-iot/service-guard.h\"'),encoding='utf-8')
make_source=m.read_text(encoding='utf-8')
anchor='OBJS += wr-iot-writer-journal.o wr-iot-bridge.o'
if make_source.count(anchor)!=1:raise SystemExit('IoT linked object anchor changed')
make_source=make_source.replace(anchor,'OBJS += wr-iot-service-guard.o wr-iot-writer-journal.o wr-iot-bridge.o',1)
if make_source.count('wr-iot-service-guard.o')!=1:raise SystemExit('IoT service guard missing or duplicated in RC link')
m.write_text(make_source,encoding='utf-8')
report['service_state_headers_installed']=True
report['service_state_lifecycle_bound']=True
report['dnsmasq_readiness']='configured-port DNS probe and lease recovery integrated; DHCP protocol readiness pending'
# Keep an owned IoT bridge blocked across normal and default firewall reloads.
# The activation controller must later replace this quarantine with verified policy.
path=rc/'firewall_ex.c';firewall=path.read_text(encoding='utf-8')
helper=r"""
#if defined(BOARD_WR1200JS)
#include "wr-iot/bridge.h"
#include "wr-iot/firewall.h"
#include "wr-iot/route-snapshot.h"
#include "wr-iot/dns-config.h"
#include "wr-iot/network-check.h"
static int wr_iot_firewall_quarantine(FILE *fp,int allow_policy,const char *lan,const char *wan)
{
 const char *keys[]={"wr_iot_gateway_t","wr_iot_mask_t","wr_iot_start_t","wr_iot_end_t"};
 char values[4][16];size_t i,n;const char *value;
 struct wr_iot_firewall rules;struct wr_iot_subnet subnet;struct wr_iot_inventory inventory;
 unsigned int index,dns_port,dhcp_port;int dhcp4;
 if(!wr_iot_bridge_is_owned())return 1;
 if(allow_policy&&nvram_get_int("wr_iot_firewall_t")==1&&nvram_get_int("wr_iot_network_t")==1&&!get_ap_mode()){
  for(i=0;i<4;i++){
   value=nvram_safe_get(keys[i]);n=strlen(value);
   if(n>=sizeof(values[i]))goto quarantine;
   memcpy(values[i],value,n+1);
  }
  /* The current policy permits standard DNS/DHCP ports only. */
  if(!wr_iot_dns_config_services_at("/etc/dnsmasq.conf",&dns_port,&dhcp4,&dhcp_port)||dns_port!=53||!dhcp4||dhcp_port!=67)goto quarantine;
  index=if_nametoindex("br-iot");
  if(!index||!wr_iot_subnet_plan(&subnet,values[0],values[1],values[2],values[3],NULL,0)||
     !wr_iot_inventory_interfaces(&inventory,1)||
     !wr_iot_route_snapshot_owned(&inventory,index,subnet.network,subnet.mask)||
     !wr_iot_firewall_plan(&rules,1,lan,wan,values[0],values[1],values[2],values[3],inventory.ranges,inventory.count))goto quarantine;
  return fputs(rules.ipv4,fp)>=0;
 }
 quarantine:
 return fputs("-A INPUT -i br-iot -j DROP\n"
              "-A FORWARD -i br-iot -j DROP\n"
              "-A FORWARD -o br-iot -j DROP\n"
              "-A INPUT -i ra2 -j DROP\n"
              "-A FORWARD -i ra2 -j DROP\n"
              "-A FORWARD -o ra2 -j DROP\n",fp)>=0;
}
static int wr_iot_nat_policy(FILE *fp,const char *wan)
{
 const char *keys[]={"wr_iot_gateway_t","wr_iot_mask_t","wr_iot_start_t","wr_iot_end_t"};
 char values[4][16],network[16],mask[16];const char *value;size_t i,n;
 struct wr_iot_subnet subnet;unsigned int dns_port,dhcp_port;int dhcp4;
 if(!wr_iot_bridge_is_owned()||nvram_get_int("wr_iot_firewall_t")!=1||nvram_get_int("wr_iot_network_t")!=1||get_ap_mode())return 1;
 if(!wan||!*wan||!wr_iot_fw_ifname(wan)||!strcmp(wan,IFNAME_BR))return 1;
 for(i=0;i<4;i++){
  value=nvram_safe_get(keys[i]);n=strlen(value);if(n>=sizeof(values[i]))return 1;memcpy(values[i],value,n+1);
 }
 if(!wr_iot_dns_config_services_at("/etc/dnsmasq.conf",&dns_port,&dhcp4,&dhcp_port)||dns_port!=53||!dhcp4||dhcp_port!=67||
    !wr_iot_network_check(values[0],values[1],values[2],values[3])||
    !wr_iot_subnet_plan(&subnet,values[0],values[1],values[2],values[3],NULL,0))return 1;
 wr_iot_fw_address(network,subnet.network);wr_iot_fw_address(mask,subnet.mask);
 return fprintf(fp,"-A POSTROUTING -s %s/%s -o %s -j MASQUERADE\n",network,mask,wan)>=0;
}

#endif

"""
anchor='#include "rc.h"'
if firewall.count(anchor)!=1:raise SystemExit('Firewall RC include anchor changed')
firewall=firewall.replace(anchor,anchor+'\n'+helper,1)
(headers/'firewall.h').write_bytes((local/'firewall.h').read_bytes())
for name,marker,result,arguments in [('ipt_filter_rules','\t// maclist chain','return 0;','1,lan_if,wan_if'),('ipt_filter_default','\t/* INPUT chain */','return;','0,NULL,NULL'),('ip6t_filter_rules','\t// maclist chain','return 0;','0,NULL,NULL'),('ip6t_filter_default','\t// INPUT chain','return;','0,NULL,NULL')]:
 begin=firewall.index('\n'+name+'(');end=firewall.index('\n}\n',begin)+3
 body=firewall[begin:end]
 if body.count(marker)!=1:raise SystemExit('Firewall rule insertion anchor changed: '+name)
 hook='#if defined(BOARD_WR1200JS)\n\tif(!wr_iot_firewall_quarantine(fp,'+arguments+')){fclose(fp);logmessage("IoT Wi-Fi","Firewall quarantine write failed");'+result+'}\n#endif\n'
 body=body.replace(marker,hook+marker,1);firewall=firewall[:begin]+body+firewall[end:]
anchor='\t\t/* masquerade WAN connection for LAN clients */'
if firewall.count(anchor)!=1:raise SystemExit('WAN NAT insertion anchor changed')
hook='#if defined(BOARD_WR1200JS)\n\t\tif(!wr_iot_nat_policy(fp,wan_if)){fclose(fp);logmessage("IoT Wi-Fi","NAT policy write failed");return 0;}\n#endif\n'
firewall=firewall.replace(anchor,hook+anchor,1)
path.write_text(firewall,encoding='utf-8')
report['iot_wan_nat']='Scoped classic MASQUERADE before existing LAN WAN NAT; requires validated internal IoT gates and WAN NAT enabled'
report['owned_bridge_firewall_quarantine']='IPv4/IPv6 normal/default builders before generic accepts; IPv4 allow policy requires wr_iot_firewall_t and wr_iot_network_t; activation controller pending'
report['iot_main_dnsmasq_config_staged']=True
report['dnsmasq_service_rollback_complete']=False
(a.source/'iot-rc-source.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS WR-only IoT bridge object and owned quiescence source integration; activation pending')

