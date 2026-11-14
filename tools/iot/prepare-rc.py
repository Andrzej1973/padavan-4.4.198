#!/usr/bin/env python3
"""Install WR-only bridge object and owned IoT quiescence before radio shutdown."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
rc=a.source/'trunk/user/rc';local=Path(__file__).parent
# User override lines are data, never printf formats. Keep this correction in
# the same prepared RC tree whose cold profile consumes AP.dat.
common=rc/'common_ex.c';common_text=common.read_text(encoding='utf-8')
begin=common_text.index('load_user_config(FILE *fp,')
end=common_text.index('\nint\nis_module_loaded',begin)
loader=common_text[begin:end]
if loader.count('fprintf(fp, line);')!=1:raise SystemExit('User config literal-write anchor changed')
loader=loader.replace('fprintf(fp, line);','fputs(line, fp);',1)
newline="line[strlen(line) - 1] = '\\n';"
if loader.count(newline)!=1:raise SystemExit('User config newline anchor changed')
# Preserve every byte, including the last byte of an unterminated value and
# chunks of a long line. A separator after the file prevents later output
# from joining an unterminated final line.
loader=loader.replace(newline,'/* Preserve input bytes; add a file separator after the read loop. */',1)
# fgets chunks are not logical lines. Decide filtering once, then preserve or
# discard every continuation of that same line. Otherwise a long comment or
# forbidden parameter can leak its tail into the generated radio profile.
declaration='char line[256], real_path[128];'
if loader.count(declaration)!=1:raise SystemExit('User config buffer anchor changed')
loader=loader.replace(declaration,declaration+'\n\tint line_start = 1, skip_line = 0;',1)
filter_begin=loader.index("\t\t\tif (line[0] == '\\0'")
filter_end=loader.index('\t\t\t/* Preserve input bytes;',filter_begin)
loader=loader[:filter_begin]+'''\t\t\tif (line_start) {
\t\t\t\tskip_line = line[0] == '\\0' || line[0] == '\\r' ||
\t\t\t\t            line[0] == '\\n' || line[0] == '#' || line[0] == ';' ||
\t\t\t\t            (forbid_list && is_param_forbidden(line, forbid_list));
\t\t\t}
\t\t\tline_start = strchr(line, '\\n') != NULL;
\t\t\tif (skip_line) continue;
\t\t\t
'''+loader[filter_end:]
close='\t\tfclose(fp_user);'
if loader.count(close)!=1:raise SystemExit('User config close anchor changed')
loader=loader.replace(close,"\t\tfputc('\\n', fp);\n"+close,1)
common.write_text(common_text[:begin]+loader+common_text[end:],encoding='utf-8')
board=a.source/'trunk/configs/boards/WR1200JS/l1profile.dat'
s=board.read_text(encoding='utf-8')
if 'INDEX0_main_ifname=ra0' not in s or 'INDEX0_ext_ifname=ra\n' not in s:raise SystemExit('WR1200JS third BSS interface assumptions changed')
f=rc/'net_wifi.c';s=f.read_text(encoding='utf-8')
anchor='void \nstop_wifi_all_rt(void)\n{'
if s.count(anchor)!=1 or 'wr_iot_quiesce' in s:raise SystemExit('Wi-Fi stop anchor changed or already prepared')
helper="""#if defined(BOARD_WR1200JS)
#include <errno.h>
#include <signal.h>
#include "wr-iot/bridge.h"
#include "wr-iot/restart-main-state.h"
#include "wr-iot/restart-guest-policy.h"
#include "wr-iot/restart-service-policy.h"
#include "wr-iot/service-guard.h"
#include "wr-iot/radio-stop-contract.h"
static int wr_iot_last_stop_result=1;
static int wr_iot_quiesce(void)
{
 /* Empty configuration or an absent bridge cannot rule out an in-flight
  * driver transaction. Only the owning controller may prove no IoT work
  * exists, or complete its safe shutdown. Never bypass it using NVRAM. */
 /* The owning activation controller must close/recover IoT while retaining
  * isolation and service ownership. Administrative DOWN is not this proof.
  * No independent bridge/gate cleanup follows this callback. */
 return wr_iot_activation_prepare_radio_stop() == 1;
}
/* Administrative AUX/Guest DOWN only. Driver completion is separately owned
 * by the physical Main transaction; no Main interface is accepted here. */
int wr_iot_rc_physical_aux_down(unsigned int slot)
{
 static const char *const names[]={IFNAME_2G_APCLI,IFNAME_2G_WDS3,
  IFNAME_2G_WDS2,IFNAME_2G_WDS1,IFNAME_2G_WDS0,IFNAME_2G_GUEST};
 if(slot>=sizeof(names)/sizeof(names[0]))return 0;
 errno=0;
 if(!if_nametoindex(names[slot]))return errno==ENODEV||errno==ENXIO;
 return wif_control(names[slot],0)==0;
}
/* Same existing Guest enable/schedule policy as normal AP startup. */
int wr_iot_rc_restart_guest_policy(int *out)
{
 int fd,enabled,before,after;
 if(!out)return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 if(get_ap_mode()||get_mode_radio_rt()!=0||get_enabled_radio_rt()!=1)return 0;
 enabled=get_enabled_guest_rt();before=is_guest_allowed_rt();
 if((enabled!=0&&enabled!=1)||(before!=0&&before!=1)||(!enabled&&before))return 0;
 after=is_guest_allowed_rt();
 if(before!=after||enabled!=get_enabled_guest_rt()||get_ap_mode()||
    get_mode_radio_rt()!=0||get_enabled_radio_rt()!=1)return 0;
 *out=before;return 1;
}
int wr_iot_rc_restart_guest_isolation_policy(int *out)
{
 int fd,before,after;
 if(!out)return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 if(get_ap_mode()||get_mode_radio_rt()!=0||get_enabled_radio_rt()!=1)return 0;
 before=nvram_wlan_get_int(0,"guest_lan_isolate");
 after=nvram_wlan_get_int(0,"guest_lan_isolate");
 if((before!=0&&before!=1)||before!=after||get_ap_mode()||
    get_mode_radio_rt()!=0||get_enabled_radio_rt()!=1)return 0;
 *out=before;return 1;
}
int is_need_8021x(char *auth_mode);
/* Mode0 restoration only. These are the existing SDK auth/RSSI operations,
 * split into checked submissions; no physical restart or WDS/APCLI activation. */
int wr_iot_rc_restart_service_policy(struct wr_iot_restart_service_policy *out)
{
 struct wr_iot_restart_service_policy p;int fd;
 if(!out)return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 if(get_ap_mode()||get_mode_radio_rt()!=0||get_enabled_radio_rt()!=1||
    !is_interface_up(IFNAME_2G_MAIN))return 0;
 p.enterprise=!!is_need_8021x(nvram_wlan_get(0,"auth_mode"));
 p.kick_rssi=nvram_get_int("rt_KickStaRssiLow");
 p.assoc_rssi=nvram_get_int("rt_AssocReqRssiThres");
 /* Validate before the vendor setter narrows simple_strtol to CHAR. */
 if(p.kick_rssi < -100||p.kick_rssi > 0||p.assoc_rssi < -100||p.assoc_rssi > 0)return 0;
 if(p.enterprise!=!!is_need_8021x(nvram_wlan_get(0,"auth_mode"))||
    p.kick_rssi!=nvram_get_int("rt_KickStaRssiLow")||
    p.assoc_rssi!=nvram_get_int("rt_AssocReqRssiThres")||get_ap_mode()||
    get_mode_radio_rt()!=0||get_enabled_radio_rt()!=1||!is_interface_up(IFNAME_2G_MAIN))return 0;
 *out=p;return 1;
}
enum wr_iot_restart_service_result wr_iot_rc_restart_service_submit(
 const struct wr_iot_restart_service_policy *expected,unsigned int slot)
{
 struct wr_iot_restart_service_policy current;int result;
 if(!expected||slot>2||!wr_iot_rc_restart_service_policy(&current)||
    current.enterprise!=expected->enterprise||current.kick_rssi!=expected->kick_rssi||
    current.assoc_rssi!=expected->assoc_rssi)return WR_SERVICE_NOT_SUBMITTED;
 if(slot==0){
  if(!current.enterprise)return WR_SERVICE_RETURNED;
  result=eval("rtinicapd","-i",IFNAME_2G_MAIN);
 }else if(slot==1)
  result=doSystem("iwpriv %s set %s=%d",IFNAME_2G_MAIN,"KickStaRssiLow",current.kick_rssi);
 else
  result=doSystem("iwpriv %s set %s=%d",IFNAME_2G_MAIN,"AssocReqRssiThres",current.assoc_rssi);
 return result?WR_SERVICE_UNCERTAIN:WR_SERVICE_RETURNED;
}
/* Process-name liveness only: not PID ownership, authentication or RSSI
 * readback. Caller must not use this alone as service completion evidence. */
int wr_iot_rc_restart_auth_process_current(const struct wr_iot_restart_service_policy *expected)
{
 struct wr_iot_restart_service_policy current;int running;
 if(!expected||!wr_iot_rc_restart_service_policy(&current)||
    current.enterprise!=expected->enterprise||current.kick_rssi!=expected->kick_rssi||
    current.assoc_rssi!=expected->assoc_rssi)return 0;
 running=pids("rtinicapd");
 if(running<0)return 0;
 return current.enterprise?running>0:running==0;
}
/* Profile generation only; never the combined stop/restart helper. */
int wr_iot_rc_restart_generate(int disable_autoscan)
{
 if(disable_autoscan!=0)return -1;
 return gen_ralink_config_2g(0);
}
#endif

"""
helper=helper.replace("/* Profile generation only;", "#include \"wr-iot/restart-auth-stop.h\"\n"+(local/"restart-auth-stop-sdk.inc").read_text()+"\n/* Profile generation only;",1)
helper=helper.replace("/* Profile generation only;", "#include \"wr-iot/restart-multicast-policy.h\"\n"+(local/"restart-multicast-policy-sdk.inc").read_text()+"\n/* Profile generation only;",1)
helper=helper.replace("/* Profile generation only;", "#include \"wr-iot/restart-radio-state.h\"\n"+(local/"restart-radio-state-sdk.inc").read_text()+"\n/* Profile generation only;",1)
s=s.replace(anchor,helper+anchor+'\n#if defined(BOARD_WR1200JS)\n wr_iot_last_stop_result=wr_iot_quiesce();\n if (!wr_iot_last_stop_result) return;\n#endif',1)
restart_anchor='void\nrestart_wifi_rt(int radio_on, int need_reload_conf)\n{'
if s.count(restart_anchor)!=1:raise SystemExit('2.4 GHz restart anchor changed')
s=s.replace(restart_anchor,restart_anchor+'''\n#if defined(BOARD_WR1200JS)
 /* Refuse profile generation/reopening if the previous IoT BSS did not stop. */
 if (!wr_iot_quiesce()) return;
#endif''',1)
begin=s.index(restart_anchor);end=s.index('\nint is_need_8021x',begin)
restart=s[begin:end]
stop_anchor='\tstop_wifi_all_rt();'
if restart.count(stop_anchor)!=1:raise SystemExit('2.4 GHz restart stop call changed')
restart=restart.replace(stop_anchor,stop_anchor+'''\n#if defined(BOARD_WR1200JS)
 if (!wr_iot_last_stop_result) return;
#endif''',1)
s=s[:begin]+restart+s[end:]

# Preserve other boards; any failed 2.4 GHz down command fences reload/open.
for interface in ('IFNAME_2G_APCLI','IFNAME_2G_WDS3','IFNAME_2G_WDS2','IFNAME_2G_WDS1','IFNAME_2G_WDS0','IFNAME_2G_GUEST','IFNAME_2G_MAIN'):
 call='wif_control('+interface+', 0);'
 begin=s.index(anchor);finish=s.index(restart_anchor,begin)
 fragment=s[begin:finish]
 if fragment.count(call)!=1:raise SystemExit('Radio down call changed: '+interface)
 replacement='#if defined(BOARD_WR1200JS)\n if(wif_control('+interface+', 0)!=0){wr_iot_last_stop_result=0;return;}\n#else\n '+call+'\n#endif'
 fragment=fragment.replace(call,replacement,1)
 s=s[:begin]+fragment+s[finish:]


# Keep every early refusal inside one balanced physical-call fence. The nested
# stop-all call obtains a LIFO token from the same process-context outer fence.
for signature,label,is_stop in ((anchor,'wr_iot_stop_done',True),(restart_anchor,'wr_iot_restart_done',False)):
 start=s.index(signature);opening=s.index('{',start);depth=1;finish=opening+1
 while depth:
  if s[finish]=='{':depth+=1
  elif s[finish]=='}':depth-=1
  finish+=1
 body=s[opening+1:finish-1]
 body=body.replace('return;','goto '+label+';')
 entry='\n#if defined(BOARD_WR1200JS)\n struct wr_iot_radio_stop_fence wr_iot_fence={0};\n if(!wr_iot_radio_stop_fence_begin(&wr_iot_fence)){wr_iot_last_stop_result=0;return;}\n#endif\n'
 exit='\n#if defined(BOARD_WR1200JS)\n'+label+':\n if(!wr_iot_radio_stop_fence_end(&wr_iot_fence))wr_iot_last_stop_result=0;\n#endif\n'
 s=s[:opening+1]+entry+body+exit+s[finish-1:]
s=s.replace('#include "wr-iot/radio-stop-contract.h"','#include "wr-iot/radio-stop-contract.h"\n#include "wr-iot/radio-stop-fence.h"',1)

m=rc/'Makefile';make=m.read_text(encoding='utf-8');anchor='OBJS += gpio_btn.o btn_action.o'
if make.count(anchor)!=1:raise SystemExit('RC object anchor changed')
make=make.replace(anchor,anchor+'\nifneq ($(findstring -DBOARD_WR1200JS,$(CFLAGS)),)\nOBJS += wr-iot-bridge.o\nendif',1)
headers=rc/'wr-iot';headers.mkdir(exist_ok=True)
for name in ('bridge.h','subnet.h','types.h'):(headers/name).write_bytes((local/name).read_bytes())
# Keep the activation state machine and the immutable request parser beside the
# RC objects that will own them.  They are still deliberately unbound here;
# staging them first makes the real RC include environment a compile gate.
for name in ('activation.h','request.h','request-stage.h','radio-profile-state.h','dns-activation.h','radio-stop-contract.h','driver-api-close-wire.h','driver-api-close-progress-wire.h','driver-api-close-release-wire.h','driver-api-open-current-wire.h','driver-api-open-recovery-wire.h','precreated-idle-wire.h'):(headers/name).write_bytes((local/name).read_bytes())
(headers/'request-snapshot.h').write_bytes((local/'request-snapshot.h').read_bytes())
snapshot=(local/'request-snapshot.c').read_text(encoding='utf-8')
for name in ('request-snapshot.h','service-guard.h','bridge.h'):
 snapshot=snapshot.replace('#include "'+name+'"','#include "wr-iot/'+name+'"',1)
(rc/'wr-iot-request-snapshot.c').write_text(snapshot,encoding='utf-8')
bridge=(local/'bridge.c').read_text(encoding='utf-8').replace('#include "bridge.h"','#include "wr-iot/bridge.h"',1).replace('#include "subnet.h"','#include "wr-iot/subnet.h"',1)
(rc/'wr-iot-bridge.c').write_text(bridge,encoding='utf-8');f.write_text(s,encoding='utf-8');m.write_text(make,encoding='utf-8')
stage=(local/'request-stage.c').read_text(encoding='utf-8').replace('#include "request-stage.h"','#include "wr-iot/request-stage.h"',1).replace('#include "request.h"','#include "wr-iot/request.h"',1)
stage=stage.replace('#include "service-guard.h"','#include "wr-iot/service-guard.h"',1)
stage=stage.replace('#include "network-check.h"','#include "wr-iot/network-check.h"',1)
stage=stage.replace('#include "bridge.h"','#include "wr-iot/bridge.h"',1)
(rc/'wr-iot-request-stage.c').write_text(stage,encoding='utf-8')
m.write_text(m.read_text(encoding='utf-8').replace('OBJS += wr-iot-bridge.o','OBJS += wr-iot-request-stage.o wr-iot-bridge.o'),encoding='utf-8')
report={'board':'WR1200JS','candidate_bss':'ra2','bridge_object_installed':True,'owned_quiescence_before_radio_stop':False,'radio_stop_controller_contract_staged':True,'radio_stop_controller_bound':False,'activation_integrated':False,'runtime_verified':False}
report['activation_headers_staged']=True
report['request_snapshot_header_staged']=True
report['request_snapshot_runtime_adapter_staged']=True
# Cold reservation is part of the one physical-radio configuration generation.
# Runtime ON/OFF must use the already-created ra2 interface; it must never use
# the old profile-rewrite/restart path.
f=rc/'ralink.c';radio=f.read_text(encoding='utf-8')
ifname_copy='strncpy(pwrq->ifr_name, ifname, IFNAMSIZ);'
if radio.count(ifname_copy)!=1:raise SystemExit('Wireless ioctl interface-copy anchor changed')
radio=radio.replace(ifname_copy,
 'if (!ifname || strlen(ifname) >= IFNAMSIZ) { close(s); return -1; }\n\tstrcpy(pwrq->ifr_name, ifname);',1)
profile_snapshot='wr_profile_wlan_get_int(is_aband, "mode_x")' in radio
anchor='static int\ngen_ralink_config('
if radio.count(anchor)!=1:raise SystemExit('Ralink generator anchor changed')
include=r'''#if defined(BOARD_WR1200JS)
#include "wr-iot/precreated-profile-request.h"
#include "wr-iot/precreated-entropy.h"
static const char *wr_iot_cold_nvram_read(void *unused,const char *key)
{
 (void)unused;
 return nvram_safe_get(key);
}
#endif

'''
if profile_snapshot:
 include=include.replace('return nvram_safe_get(key);','return wr_profile_safe_get(key);')
radio=radio.replace(anchor,include+anchor,1)
decl='int i_stream_tx, i_stream_rx, i_mphy, i_mmcs, i_fphy[2], i_val_mbss[2];'
if radio.count(decl)!=1:raise SystemExit('Ralink local declaration changed')
radio=radio.replace(decl,decl+'''\n\tint iot_reserved = 0;\n#if defined(BOARD_WR1200JS)\n\tstruct wr_iot_precreated_profile_request iot_request;\n#endif''',1)
anchor='\ti_mode_x = nvram_wlan_get_int(is_aband, "mode_x");'
if profile_snapshot:anchor=anchor.replace('nvram_wlan_get_int','wr_profile_wlan_get_int')
if radio.count(anchor)!=1:raise SystemExit('Ralink radio-mode anchor changed')
cold=r'''\ti_mode_x = nvram_wlan_get_int(is_aband, "mode_x");
#if defined(BOARD_WR1200JS)
\t/* Reserve ra2 only while generating the initial 2.4 GHz AP profile.
\t * An unavailable CSPRNG or invalid saved request leaves BssidNum at two:
\t * never create an open fallback BSS. MBSS_Open controls beacon emission;
\t * net_wifi deliberately does not ifconfig ra2 up until IoT activation. */
\tif (!is_aband && is_soc_ap && i_mode_x != 1 && i_mode_x != 3 &&
\t    wr_iot_precreated_boot_request_read(&iot_request,
\t      wr_iot_cold_nvram_read, NULL, wr_iot_precreated_entropy, NULL)) {
\t\ti_ssid_num = 3;
\t\tiot_reserved = 1;
\t}
#endif'''
cold=cold.replace(r'\t','\t')
if profile_snapshot:cold=cold.replace('nvram_wlan_get_int','wr_profile_wlan_get_int')
radio=radio.replace(anchor,cold,1)
replacements=[
 ('fprintf(fp, "SSID%d=%s\\n", 2, nvram_wlan_get(is_aband, "guest_ssid"));', 'fprintf(fp, "SSID%d=%s\\n", 2, nvram_wlan_get(is_aband, "guest_ssid"));\n#if defined(BOARD_WR1200JS)\n\tif (iot_reserved) fprintf(fp, "SSID%d=%s\\n", 3, iot_request.ssid);\n#endif'),
 ('for (i = 3; i <= 8; i++)\n\t\tfprintf(fp, "SSID%d=%s\\n", i, "");', 'for (i = iot_reserved ? 4 : 3; i <= 8; i++)\n\t\tfprintf(fp, "SSID%d=%s\\n", i, "");'),
 ('fprintf(fp, "WmmCapable=%d;%d\\n", i_wmm, i_wmm);', 'fprintf(fp, "WmmCapable=%d;%d%s\\n", i_wmm, i_wmm, iot_reserved ? ";1" : "");'),
 ('fprintf(fp, "DLSCapable=%d;%d\\n", 0, 0);', 'fprintf(fp, "DLSCapable=%d;%d%s\\n", 0, 0, iot_reserved ? ";0" : "");'),
 ('fprintf(fp, "NoForwarding=%d;%d\\n", i_val_mbss[0], i_val_mbss[1]);', 'fprintf(fp, "NoForwarding=%d;%d%s\\n", i_val_mbss[0], i_val_mbss[1], iot_reserved ? ";1" : "");'),
 ('fprintf(fp, "NoForwardingMBCast=%d;%d\\n", i_val_mbss[0], i_val_mbss[1]);', 'fprintf(fp, "NoForwardingMBCast=%d;%d%s\\n", i_val_mbss[0], i_val_mbss[1], iot_reserved ? ";1" : "");'),
 ('fprintf(fp, "HideSSID=%d;%d\\n", i_val_mbss[0], i_val_mbss[1]);', 'fprintf(fp, "HideSSID=%d;%d%s\\n", i_val_mbss[0], i_val_mbss[1], iot_reserved ? ";0" : "");'),
 ('fprintf(fp, "PreAuth=0;0\\n");', 'fprintf(fp, "PreAuth=0;0%s\\n", iot_reserved ? ";0" : "");'),
 ('fprintf(fp, "IEEE8021X=%d;%d\\n", i_val, 0);', 'fprintf(fp, "IEEE8021X=%d;%d%s\\n", i_val, 0, iot_reserved ? ";0" : "");'),
 ('fprintf(fp, "FixedTxMode=%d;%d\\n", i_fphy[0], i_fphy[1]);', 'fprintf(fp, "FixedTxMode=%d;%d%s\\n", i_fphy[0], i_fphy[1], iot_reserved ? ";0" : "");'),
 ('fprintf(fp, "HT_MCS=%d;%d\\n", i_val_mbss[0], i_val_mbss[1]);', 'fprintf(fp, "HT_MCS=%d;%d%s\\n", i_val_mbss[0], i_val_mbss[1], iot_reserved ? ";33" : "");'),
 ('fprintf(fp, "StationKeepAlive=%d;%d\\n", 0, 0);', 'fprintf(fp, "StationKeepAlive=%d;%d%s\\n", 0, 0, iot_reserved ? ";0" : "");'),
 ('fprintf(fp, "AuthMode=%s;%s\\n", c_val_mbss[0], c_val_mbss[1]);', 'fprintf(fp, "AuthMode=%s;%s%s\\n", c_val_mbss[0], c_val_mbss[1], iot_reserved ? ";WPA2PSK" : "");'),
 ('fprintf(fp, "EncrypType=%s;%s\\n", c_val_mbss[0], c_val_mbss[1]);', 'fprintf(fp, "EncrypType=%s;%s%s\\n", c_val_mbss[0], c_val_mbss[1], iot_reserved ? ";AES" : "");'),
 ('fprintf(fp, "WPAPSK%d=%s\\n", 2, nvram_wlan_get(is_aband, "guest_wpa_psk"));', 'fprintf(fp, "WPAPSK%d=%s\\n", 2, nvram_wlan_get(is_aband, "guest_wpa_psk"));\n#if defined(BOARD_WR1200JS)\n\tif (iot_reserved) fprintf(fp, "WPAPSK%d=%s\\n", 3, iot_request.password);\n#endif'),
 ('for (i = 3; i <= 8; i++)\n\t\tfprintf(fp, "WPAPSK%d=%s\\n", i, "");', 'for (i = iot_reserved ? 4 : 3; i <= 8; i++)\n\t\tfprintf(fp, "WPAPSK%d=%s\\n", i, "");'),
]
for old,new in replacements:
 if profile_snapshot:
  old=old.replace('nvram_wlan_get(','wr_profile_wlan_get(')
  new=new.replace('nvram_wlan_get(','wr_profile_wlan_get(')
 if radio.count(old)!=1:raise SystemExit('Cold BSS output anchor changed: '+old)
 radio=radio.replace(old,new,1)
# SDK generator otherwise ignores stream errors. Preserve other boards/bands;
# fail WR SoC2g generation so its retained file owner can recover the baseline.
iot_generator_checked_close = """#if defined(BOARD_WR1200JS)
	if (!is_aband && is_soc_ap) {
		int wr_iot_io_failed = ferror(fp) != 0;
		if (fflush(fp) != 0) wr_iot_io_failed = 1;
		if (fclose(fp) != 0) wr_iot_io_failed = 1;
		return wr_iot_io_failed ? -1 : 0;
	}
#endif
	fclose(fp);

	return 0;"""
def checked_generator_tail(radio):
 plain='\tfclose(fp);\n\n\treturn 0;\n}\n\nint\ngen_ralink_config_2g'
 band='\tfclose(fp);\n\treturn 0;\n#endif\n}\n\nint\ngen_ralink_config_2g'
 # Band Steering already checks its enabled branch. Add WR2g checks only
 # to its fallback branch, preserving the existing coordinated writer.
 matches=radio.count(plain)+radio.count(band)
 if matches!=1:raise SystemExit('Ralink generator close anchor changed')
 if plain in radio:return radio.replace(plain,iot_generator_checked_close+'\n}\n\nint\ngen_ralink_config_2g',1)
 return radio.replace(band,iot_generator_checked_close+'\n#endif\n}\n\nint\ngen_ralink_config_2g',1)
radio=checked_generator_tail(radio)
for name in ('profile.h','profile-list.h','profile-line.h','profile-scan.h','profile-stream.h','profile-file.h','precreated-profile-request.h','precreated-entropy.h'):
 (headers/name).write_bytes((local/name).read_bytes())
shared=rc/'shared-wifi';shared.mkdir(exist_ok=True)
(shared/'validate.h').write_bytes((local.parent/'shared-wifi/validate.h').read_bytes())
profile=(local/'profile.c').read_text(encoding='utf-8').replace('#include "profile.h"','#include "wr-iot/profile.h"').replace('#include "profile-file.h"','#include "wr-iot/profile-file.h"')
(rc/'wr-iot-profile.c').write_text(profile,encoding='utf-8')
m.write_text(m.read_text(encoding='utf-8').replace('OBJS += wr-iot-request-stage.o wr-iot-bridge.o','OBJS += wr-iot-request-stage.o wr-iot-bridge.o wr-iot-profile.o'),encoding='utf-8')
f.write_text(radio,encoding='utf-8')
report['profile_generator_checked_io']=True
report['profile_hook_installed']=True
report['profile_activation_guard']='cold generator only; runtime backend remains unbound'
report['profile_owned_removal_api_installed']=True
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
for name in ('network-check.h','bridge.h','route-snapshot.h','subnet.h','dns-ready.h','dhcp-ready.h','dns-sockets.h'):
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
controller=(local/"restart-controller.inc").read_text(encoding="utf-8").replace('#include "dns-ready.h"','#include "wr-iot/dns-ready.h"').replace('#include "dns-config.h"','#include "wr-iot/dns-config.h"').replace('#include "dhcp-ready.h"','#include "wr-iot/dhcp-ready.h"').replace('#include "dns-sockets.h"','#include "wr-iot/dns-sockets.h"').replace('#include "bridge.h"','#include "wr-iot/bridge.h"')
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
# The controller above binds the journal only inside the gated DNS transaction;
# outside that transaction, the legacy unbound behavior remains unchanged.
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
report['writer_journal_transaction_binding_installed']=True
report['writer_journal_transaction_binding_scope']=(
 'Conditional DNS restart transaction only; the IoT startup/activation path '
 'does not set the network gate, and not all DNS-related writers are covered'
)
(headers/'writer-journal.h').write_bytes((local/'writer-journal.h').read_bytes())
(rc/'wr-iot-writer-journal.c').write_text((local/'writer-journal.c').read_text(encoding='utf-8').replace('#include "writer-journal.h"','#include "wr-iot/writer-journal.h"').replace('#include "service-state.h"','#include "wr-iot/service-state.h"'),encoding='utf-8')
m.write_text(m.read_text(encoding='utf-8').replace('OBJS += wr-iot-request-stage.o wr-iot-bridge.o wr-iot-profile.o wr-iot-dhcp.o wr-iot-network.o','OBJS += wr-iot-request-stage.o wr-iot-writer-journal.o wr-iot-bridge.o wr-iot-profile.o wr-iot-dhcp.o wr-iot-network.o'),encoding='utf-8')

for name in ('service-state.h','service-transaction.h','service-lock.h','dnsmasq-files.h','saved-bundle.h','saved-file.h','restore-file.h','uts-state.h','arp-state.h','arp-restore.h'):
 (headers/name).write_bytes((local/name).read_bytes())
(headers/'service-guard.h').write_bytes((local/'service-guard.h').read_bytes())
(rc/'wr-iot-service-guard.c').write_text((local/'service-guard.c').read_text(encoding='utf-8').replace('#include \"service-lock.h\"','#include \"wr-iot/service-lock.h\"').replace('#include \"service-guard.h\"','#include \"wr-iot/service-guard.h\"'),encoding='utf-8')
make_source=m.read_text(encoding='utf-8')
anchor='OBJS += wr-iot-request-stage.o wr-iot-writer-journal.o wr-iot-bridge.o wr-iot-profile.o wr-iot-dhcp.o wr-iot-network.o'
if make_source.count(anchor)!=1:raise SystemExit('IoT linked object anchor changed')
make_source=make_source.replace(anchor,'OBJS += wr-iot-request-stage.o wr-iot-service-guard.o wr-iot-writer-journal.o wr-iot-bridge.o wr-iot-profile.o wr-iot-dhcp.o wr-iot-network.o',1)
make_source=make_source.replace('OBJS += wr-iot-request-stage.o','OBJS += wr-iot-request-snapshot.o wr-iot-request-stage.o',1)
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
static int wr_iot_active_filter_plan(struct wr_iot_firewall *rules,const char *lan,const char *wan)
{
 const char *keys[]={"wr_iot_gateway_t","wr_iot_mask_t","wr_iot_start_t","wr_iot_end_t"};
 char values[4][16];size_t i,n;const char *value;
 struct wr_iot_subnet subnet;struct wr_iot_inventory inventory;
 unsigned int index,dns_port,dhcp_port;int dhcp4;
 if(!wr_iot_bridge_is_owned())return 0;
 if(nvram_get_int("wr_iot_firewall_t")==1&&nvram_get_int("wr_iot_network_t")==1&&!get_ap_mode()){
  for(i=0;i<4;i++){
   value=nvram_safe_get(keys[i]);n=strlen(value);
   if(n>=sizeof(values[i]))return 0;
   memcpy(values[i],value,n+1);
  }
  /* The current policy permits standard DNS/DHCP ports only. */
  if(!wr_iot_dns_config_services_at("/etc/dnsmasq.conf",&dns_port,&dhcp4,&dhcp_port)||dns_port!=53||!dhcp4||dhcp_port!=67)return 0;
  index=if_nametoindex("br-iot");
  if(!index||!wr_iot_subnet_plan(&subnet,values[0],values[1],values[2],values[3],NULL,0)||
     !wr_iot_inventory_interfaces(&inventory,1)||
     !wr_iot_route_snapshot_owned(&inventory,index,subnet.network,subnet.mask)||
     !wr_iot_firewall_plan(rules,1,lan,wan,values[0],values[1],values[2],values[3],inventory.ranges,inventory.count))return 0;
  return 1;
 }
 return 0;
}
static int wr_iot_firewall_quarantine(FILE *fp,int allow_policy,const char *lan,const char *wan)
{
 struct wr_iot_firewall rules;
 /* ra2 is reserved for the third BSS on this board. Keep it quarantined
  * even before br-iot ownership is established; a partially attached BSS
  * must not inherit broad router/LAN accept rules. */
 if(!wr_iot_bridge_is_owned())
  return fputs("-A INPUT -i ra2 -j DROP\n"
               "-A FORWARD -i ra2 -j DROP\n"
               "-A FORWARD -o ra2 -j DROP\n",fp)>=0;
 /* Keep an unbridged ra2 path blocked after the br-iot allow policy is
  * installed too. Routed IoT packets use br-iot as their ingress device. */
 if(allow_policy&&wr_iot_active_filter_plan(&rules,lan,wan))
  return fputs("-A INPUT -i ra2 -j DROP\n"
               "-A FORWARD -i ra2 -j DROP\n"
               "-A FORWARD -o ra2 -j DROP\n",fp)>=0 && fputs(rules.ipv4,fp)>=0;
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
(headers/'quarantine-check.h').write_bytes((local/'quarantine-check.h').read_bytes())
(headers/'quarantine-live.h').write_bytes((local/'quarantine-live.h').read_bytes())
(headers/'policy-normalize.h').write_bytes((local/'policy-normalize.h').read_bytes())
(headers/'policy-check.h').write_bytes((local/'policy-check.h').read_bytes())
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
report['dns_disable_transaction_api_installed']=True
report['owned_disable_settings_api_installed']=True
(headers/'disable-services.h').write_bytes((local/'disable-services.h').read_bytes())
disable=(local/'disable-services.c').read_text(encoding='utf-8')
for name in ('disable-services.h','dns-activation.h','quarantine.h'):
 disable=disable.replace('#include "'+name+'"','#include "wr-iot/'+name+'"',1)
(rc/'wr-iot-disable-services.c').write_text(disable,encoding='utf-8')
make=m.read_text(encoding='utf-8')
if make.count('wr-iot-request-snapshot.o')!=1:raise SystemExit('Disable service object anchor changed')
m.write_text(make.replace('wr-iot-request-snapshot.o','wr-iot-request-snapshot.o wr-iot-disable-services.o',1),encoding='utf-8')
report['disable_services_adapter_installed']=True
report['disable_services_controller_bound']=False
(headers/'disable-controller.h').write_bytes((local/'disable-controller.h').read_bytes())
disable=(local/'disable-controller.c').read_text(encoding='utf-8')
for name in ('disable-controller.h','bridge.h'):
 disable=disable.replace('#include "'+name+'"','#include "wr-iot/'+name+'"',1)
(rc/'wr-iot-disable-controller.c').write_text(disable,encoding='utf-8')
make=m.read_text(encoding='utf-8')
if make.count('wr-iot-disable-services.o')!=1:raise SystemExit('Disable controller object anchor changed')
m.write_text(make.replace('wr-iot-disable-services.o','wr-iot-disable-services.o wr-iot-disable-controller.o',1),encoding='utf-8')
report['disable_controller_adapter_installed']=True
report['disable_controller_radio_bound']=False
report['dns_disable_scope']='Fresh current service snapshot before bridge removal; exact closed gates, DOWN BSS and absent/owned bridge; bounded include graph must contain no owned IoT markers before commit; activation callback binding pending'
(headers/'quarantine.h').write_bytes((local/'quarantine.h').read_bytes())
quarantine=(local/'quarantine.c').read_text(encoding='utf-8')
for name in ('quarantine.h','quarantine-live.h','bridge.h','service-guard.h'):
 quarantine=quarantine.replace('#include "'+name+'"','#include "wr-iot/'+name+'"')
(rc/'wr-iot-quarantine.c').write_text(quarantine,encoding='utf-8')
make=m.read_text(encoding='utf-8')
if make.count('wr-iot-network.o')!=1:raise SystemExit('Quarantine object link anchor changed')
make=make.replace('wr-iot-network.o','wr-iot-network.o wr-iot-quarantine.o\nLDFLAGS += -lrt',1)
m.write_text(make,encoding='utf-8')
report['quarantine_readback_object_linked']=True
firewall=path.read_text(encoding='utf-8')
if 'int wr_iot_quarantine_apply(void)' in firewall:raise SystemExit('Quarantine apply already installed')
firewall+='\n'+(local/'quarantine-apply.inc').read_text(encoding='utf-8')
path.write_text(firewall,encoding='utf-8')
report['quarantine_checked_apply_installed']=True
# Linux API transport is linked only in this isolated prepared RC. Activation
# still requires the driver's ownership/readback and network recovery backend.
for name in ('driver-api-client.h','driver-api-wire.h'):
 (headers/name).write_bytes((local/name).read_bytes())
client=(local/'driver-api-client.c').read_text(encoding='utf-8')
client=client.replace('#include "driver-api-client.h"','#include "wr-iot/driver-api-client.h"',1)
(rc/'wr-iot-driver-api-client.c').write_text(client,encoding='utf-8')
make=m.read_text(encoding='utf-8')
if make.count('wr-iot-disable-controller.o')!=1:raise SystemExit('Driver API client object anchor changed')
m.write_text(make.replace('wr-iot-disable-controller.o','wr-iot-disable-controller.o wr-iot-driver-api-client.o',1),encoding='utf-8')
(headers/'driver-close-controller.h').write_bytes((local/'driver-close-controller.h').read_bytes())
close_controller=(local/'driver-close-controller.c').read_text(encoding='utf-8')
close_controller=close_controller.replace('#include "driver-close-controller.h"','#include "wr-iot/driver-close-controller.h"',1)
(rc/'wr-iot-driver-close-controller.c').write_text(close_controller,encoding='utf-8')
make=m.read_text(encoding='utf-8')
if make.count('wr-iot-driver-api-client.o')!=1:raise SystemExit('Driver close controller object anchor changed')
m.write_text(make.replace('wr-iot-driver-api-client.o','wr-iot-driver-api-client.o wr-iot-driver-close-controller.o',1),encoding='utf-8')
(headers/'precreated-stop.h').write_bytes((local/'precreated-stop.h').read_bytes())
stop_owner=(local/'precreated-stop.c').read_text(encoding='utf-8')
for name in ('precreated-stop.h','service-guard.h','bridge.h'):
 stop_owner=stop_owner.replace('#include "'+name+'"','#include "wr-iot/'+name+'"',1)
(rc/'wr-iot-precreated-stop.c').write_text(stop_owner,encoding='utf-8')
make=m.read_text(encoding='utf-8')
if make.count('wr-iot-driver-close-controller.o')!=1:raise SystemExit('Precreated stop object anchor changed')
m.write_text(make.replace('wr-iot-driver-close-controller.o','wr-iot-driver-close-controller.o wr-iot-precreated-stop.o',1),encoding='utf-8')
(headers/'driver-open-controller.h').write_bytes((local/'driver-open-controller.h').read_bytes())
open_owner=(local/'driver-open-controller.c').read_text(encoding='utf-8')
for name in ('driver-open-controller.h','request-stage.h','service-guard.h','network-check.h','bridge.h','quarantine.h'):
 open_owner=open_owner.replace('#include "'+name+'"','#include "wr-iot/'+name+'"',1)
(rc/'wr-iot-driver-open-controller.c').write_text(open_owner,encoding='utf-8')
make=m.read_text(encoding='utf-8')
if make.count('wr-iot-precreated-stop.o')!=1:raise SystemExit('Driver OPEN controller object anchor changed')
m.write_text(make.replace('wr-iot-precreated-stop.o','wr-iot-precreated-stop.o wr-iot-driver-open-controller.o',1),encoding='utf-8')
for name in ('start-admission.h','rc-shutdown-admission.h'):
 (headers/name).write_bytes((local/name).read_bytes())
admission=(local/'start-admission.c').read_text(encoding='utf-8')
for name in ('start-admission.h','request-stage.h','driver-api-client.h','service-guard.h','rc-shutdown-admission.h'):
 admission=admission.replace('#include "'+name+'"','#include "wr-iot/'+name+'"',1)
(rc/'wr-iot-start-admission.c').write_text(admission,encoding='utf-8')
make=m.read_text(encoding='utf-8')
if make.count('wr-iot-driver-open-controller.o')!=1:raise SystemExit('Startup admission object anchor changed')
m.write_text(make.replace('wr-iot-driver-open-controller.o','wr-iot-driver-open-controller.o wr-iot-start-admission.o',1),encoding='utf-8')
(headers/'start-network.h').write_bytes((local/'start-network.h').read_bytes())
network_start=(local/'start-network.c').read_text(encoding='utf-8')
for name in ('start-network.h', 'driver-api-client.h', 'service-guard.h', 'rc-shutdown-admission.h', 'bridge.h', 'network-check.h', 'request-stage.h', 'quarantine.h', 'dns-activation.h'):
 network_start=network_start.replace('#include "'+name+'"','#include "wr-iot/'+name+'"',1)
(rc/'wr-iot-start-network.c').write_text(network_start,encoding='utf-8')
make=m.read_text(encoding='utf-8')
if make.count('wr-iot-start-admission.o')!=1:raise SystemExit('Startup network object anchor changed')
m.write_text(make.replace('wr-iot-start-admission.o','wr-iot-start-admission.o wr-iot-start-network.o',1),encoding='utf-8')
(headers/'start-network-rollback.h').write_bytes((local/'start-network-rollback.h').read_bytes())
rollback=(local/'start-network-rollback.c').read_text(encoding='utf-8')
for name in ('start-network-rollback.h', 'driver-api-client.h', 'service-guard.h', 'rc-shutdown-admission.h', 'bridge.h', 'dns-activation.h'):
 rollback=rollback.replace('#include "'+name+'"','#include "wr-iot/'+name+'"',1)
(rc/'wr-iot-start-network-rollback.c').write_text(rollback,encoding='utf-8')
make=m.read_text(encoding='utf-8')
if make.count('wr-iot-start-network.o')!=1:raise SystemExit('Startup rollback object anchor changed')
m.write_text(make.replace('wr-iot-start-network.o','wr-iot-start-network.o wr-iot-start-network-rollback.o',1),encoding='utf-8')
report['start_network_rollback_staged']=True
report['start_network_rollback_runtime_bound']=False
(headers/'start-close.h').write_bytes((local/'start-close.h').read_bytes())
unit=(local/'start-close.c').read_text(encoding='utf-8')
for name in ('start-close.h', 'service-guard.h', 'rc-shutdown-admission.h'):
 unit=unit.replace('#include "'+name+'"','#include "wr-iot/'+name+'"',1)
(rc/'wr-iot-start-close.c').write_text(unit,encoding='utf-8')
make=m.read_text(encoding='utf-8')
if make.count('wr-iot-start-network-rollback.o')!=1:raise SystemExit('Post-CLOSE object anchor changed')
m.write_text(make.replace('wr-iot-start-network-rollback.o','wr-iot-start-network-rollback.o wr-iot-start-close.o',1),encoding='utf-8')
report['start_close_staged']=True
report['start_close_runtime_bound']=False
(headers/'start-closed-rollback.h').write_bytes((local/'start-closed-rollback.h').read_bytes())
unit=(local/'start-closed-rollback.c').read_text(encoding='utf-8')
for name in ('start-closed-rollback.h', 'driver-api-client.h', 'service-guard.h', 'rc-shutdown-admission.h', 'bridge.h', 'dns-activation.h'):
 unit=unit.replace('#include "'+name+'"','#include "wr-iot/'+name+'"',1)
(rc/'wr-iot-start-closed-rollback.c').write_text(unit,encoding='utf-8')
make=m.read_text(encoding='utf-8')
if make.count('wr-iot-start-network-rollback.o')!=1:raise SystemExit('Post-CLOSE object anchor changed')
m.write_text(make.replace('wr-iot-start-network-rollback.o','wr-iot-start-network-rollback.o wr-iot-start-closed-rollback.o',1),encoding='utf-8')
report['start_closed_rollback_staged']=True
report['start_closed_rollback_runtime_bound']=False
(headers/'start-commit.h').write_bytes((local/'start-commit.h').read_bytes())
unit=(local/'start-commit.c').read_text(encoding='utf-8')
for name in ('start-commit.h', 'service-guard.h', 'rc-shutdown-admission.h', 'request-stage.h', 'network-check.h', 'quarantine.h', 'dns-activation.h'):
 unit=unit.replace('#include "'+name+'"','#include "wr-iot/'+name+'"',1)
(rc/'wr-iot-start-commit.c').write_text(unit,encoding='utf-8')
make=m.read_text(encoding='utf-8')
if make.count('wr-iot-start-close.o')!=1:raise SystemExit('Startup commit object anchor changed')
m.write_text(make.replace('wr-iot-start-close.o','wr-iot-start-close.o wr-iot-start-commit.o',1),encoding='utf-8')
report['start_commit_staged']=True
report['start_commit_runtime_bound']=False
(headers/'control-record.h').write_bytes((local/'control-record.h').read_bytes())
(headers/'start-runner.h').write_bytes((local/'start-runner.h').read_bytes())
unit=(local/'start-runner.c').read_text(encoding='utf-8')
for name in ('start-runner.h','rc-shutdown-admission.h','reopen-start.h','reopen-network.h','reopen-rollback.h'):
 unit=unit.replace('#include "'+name+'"','#include "wr-iot/'+name+'"',1)
(rc/'wr-iot-start-runner.c').write_text(unit,encoding='utf-8')
make=m.read_text(encoding='utf-8')
if make.count('wr-iot-start-commit.o')!=1:raise SystemExit('Startup runner object anchor changed')
m.write_text(make.replace('wr-iot-start-commit.o','wr-iot-start-commit.o wr-iot-start-runner.o',1),encoding='utf-8')
report['start_runner_staged']=True
report['start_runner_runtime_bound']=False

(headers/'active-stop.h').write_bytes((local/'active-stop.h').read_bytes())
unit=(local/'active-stop.c').read_text(encoding='utf-8')
for name in ('active-stop.h','rc-shutdown-admission.h'):
 unit=unit.replace('#include "'+name+'"','#include "wr-iot/'+name+'"',1)
(rc/'wr-iot-active-stop.c').write_text(unit,encoding='utf-8')
make=m.read_text(encoding='utf-8')
if make.count('wr-iot-start-runner.o')!=1:raise SystemExit('Active stop object anchor changed')
m.write_text(make.replace('wr-iot-start-runner.o','wr-iot-start-runner.o wr-iot-active-stop.o',1),encoding='utf-8')
report['active_stop_staged']=True
report['active_stop_runtime_bound']=False

(headers/'activation-owner.h').write_bytes((local/'activation-owner.h').read_bytes())
unit=(local/'activation-owner.c').read_text(encoding='utf-8')
for name in ('activation-owner.h','rc-shutdown-admission.h','reopen-admission.h','service-guard.h','bridge.h','dns-activation.h'):
 unit=unit.replace('#include "'+name+'"','#include "wr-iot/'+name+'"',1)
(rc/'wr-iot-activation-owner.c').write_text(unit,encoding='utf-8')
make=m.read_text(encoding='utf-8')
if make.count('wr-iot-active-stop.o')!=1:raise SystemExit('Activation owner object anchor changed')
m.write_text(make.replace('wr-iot-active-stop.o','wr-iot-active-stop.o wr-iot-activation-owner.o',1),encoding='utf-8')
report['activation_owner_staged']=True
report['activation_owner_runtime_bound']=False

(headers/'activation-observe.h').write_bytes((local/'activation-observe.h').read_bytes())
unit=(local/'activation-observe.c').read_text(encoding='utf-8')
for name in ('activation-observe.h','service-guard.h','request-stage.h','network-check.h','bridge.h','quarantine.h','dns-activation.h'):
 unit=unit.replace('#include "'+name+'"','#include "wr-iot/'+name+'"',1)
(rc/'wr-iot-activation-observe.c').write_text(unit,encoding='utf-8')
make=m.read_text(encoding='utf-8')
if make.count('wr-iot-activation-owner.o')!=1:raise SystemExit('Activation observer object anchor changed')
m.write_text(make.replace('wr-iot-activation-owner.o','wr-iot-activation-owner.o wr-iot-activation-observe.o',1),encoding='utf-8')
report['activation_observer_staged']=True
report['activation_observer_runtime_bound']=False

(headers/'initial-off.h').write_bytes((local/'initial-off.h').read_bytes())
unit=(local/'initial-off.c').read_text(encoding='utf-8')
for name in ('initial-off.h','request-snapshot.h','service-guard.h','rc-shutdown-admission.h','driver-api-client.h','bridge.h','dns-activation.h'):
 unit=unit.replace('#include "'+name+'"','#include "wr-iot/'+name+'"',1)
(rc/'wr-iot-initial-off.c').write_text(unit,encoding='utf-8')
make=m.read_text(encoding='utf-8')
if make.count('wr-iot-activation-observe.o')!=1:raise SystemExit('Initial OFF object anchor changed')
m.write_text(make.replace('wr-iot-activation-observe.o','wr-iot-activation-observe.o wr-iot-initial-off.o',1),encoding='utf-8')
report['initial_off_staged']=True
report['initial_off_runtime_bound']=False




report['start_network_staged']=True
report['start_network_runtime_bound']=False
report['start_admission_staged']=True
report['start_admission_runtime_bound']=False
report['driver_open_controller_staged']=True
report['driver_open_controller_bound']=False
report['precreated_stop_owner_staged']=True
report['precreated_stop_runtime_bound']=False
report['linux_driver_close_controller_staged']=True
report['linux_driver_api_client_staged']=True
report['linux_driver_api_client_activation_bound']=False
# Reopen sources retain the old CLOSED witness until new OPEN submission.
for name in ('reopen-witness.h','reopen-admission.h','reopen-start.h','reopen-network.h','reopen-rollback.h'):
 (headers/name).write_bytes((local/name).read_bytes())
for stem,names in (('reopen-admission', ('reopen-admission.h', 'service-guard.h', 'request-snapshot.h', 'bridge.h', 'dns-activation.h')), ('reopen-start', ('reopen-start.h', 'request-stage.h', 'service-guard.h', 'rc-shutdown-admission.h')), ('reopen-network', ('reopen-network.h', 'driver-api-client.h', 'service-guard.h', 'rc-shutdown-admission.h', 'bridge.h', 'network-check.h', 'request-stage.h', 'quarantine.h', 'dns-activation.h')), ('reopen-rollback', ('reopen-rollback.h', 'driver-api-client.h', 'service-guard.h', 'rc-shutdown-admission.h', 'bridge.h', 'dns-activation.h'))):
 unit=(local/(stem+'.c')).read_text(encoding='utf-8')
 for name in names:
  unit=unit.replace('#include "'+name+'"','#include "wr-iot/'+name+'"',1)
 (rc/('wr-iot-'+stem+'.c')).write_text(unit,encoding='utf-8')
make=m.read_text(encoding='utf-8')
if make.count('wr-iot-initial-off.o')!=1:raise SystemExit('Reopen object anchor changed')
objects=' '.join('wr-iot-'+stem+'.o' for stem,names in (('reopen-admission', ('reopen-admission.h', 'service-guard.h', 'request-snapshot.h', 'bridge.h', 'dns-activation.h')), ('reopen-start', ('reopen-start.h', 'request-stage.h', 'service-guard.h', 'rc-shutdown-admission.h')), ('reopen-network', ('reopen-network.h', 'driver-api-client.h', 'service-guard.h', 'rc-shutdown-admission.h', 'bridge.h', 'network-check.h', 'request-stage.h', 'quarantine.h', 'dns-activation.h')), ('reopen-rollback', ('reopen-rollback.h', 'driver-api-client.h', 'service-guard.h', 'rc-shutdown-admission.h', 'bridge.h', 'dns-activation.h'))))
m.write_text(make.replace('wr-iot-initial-off.o','wr-iot-initial-off.o '+objects,1),encoding='utf-8')
(headers/'restart-guest-policy.h').write_bytes((local/'restart-guest-policy.h').read_bytes())
(headers/'restart-service-policy.h').write_bytes((local/'restart-service-policy.h').read_bytes())
(headers/'restart-auth-stop.h').write_bytes((local/'restart-auth-stop.h').read_bytes())
(headers/'restart-radio-state.h').write_bytes((local/'restart-radio-state.h').read_bytes())
(headers/'restart-multicast-policy.h').write_bytes((local/'restart-multicast-policy.h').read_bytes())
(headers/'restart-main-state.h').write_bytes((local/'restart-main-state.h').read_bytes())
(headers/'radio-stop-fence.h').write_bytes((local/'radio-stop-fence.h').read_bytes())
unit=(local/'radio-stop-fence.c').read_text()
for name in ('radio-stop-fence.h','rc-shutdown-admission.h'):
 unit=unit.replace('#include "'+name+'"','#include "wr-iot/'+name+'"',1)
(rc/'wr-iot-radio-stop-fence.c').write_text(unit)
make=m.read_text()
if make.count('wr-iot-initial-off.o')!=1:raise SystemExit('Radio fence object anchor changed')
m.write_text(make.replace('wr-iot-initial-off.o','wr-iot-initial-off.o wr-iot-radio-stop-fence.o',1))
report['radio_stop_fence_staged']=True
report['reopen_staged']=True
report['reopen_runtime_bound']=False

(a.source/'iot-rc-source.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS WR-only IoT bridge and controller stop contract staged; controller/activation backend remains unbound')

