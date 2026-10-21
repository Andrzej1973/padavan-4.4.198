#!/usr/bin/env python3
"""Remove legacy VPN userspace packages from the WR1200JS source build.

Preserve PPP/PPPoE and shared crypto. Legacy start requests are rejected; further kernel/UI pruning is separate.
"""
import argparse
import re
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent / 'vpn-profiles'))
from type_ui import remove_unavailable_vpn_types
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
a=p.parse_args();root=a.source/'trunk/user'
changes={
 'Makefile': [('dir_y\t\t\t\t\t\t+= poptop\n',''),
              ('dir_y\t\t\t\t\t\t+= xl2tpd\n','')],
 'pppd/pppd/plugins/Makefile': [('SUBDIRS := rp-pppoe pppol2tp pptp','SUBDIRS := rp-pppoe')],
 'pppd/Makefile': [
 ('\t$(ROMFSINST) -d pppd/plugins/pppol2tp/pppol2tp.so /usr/lib/pppd/pppol2tp.so\n',''),
 ('\t$(ROMFSINST) -d pppd/plugins/pptp/pptp.so /usr/lib/pppd/pptp.so\n','')],
}
# Refuse stale legacy requests before side effects; retain saved NVRAM values.
for role,result in [('vpnc','1'),('vpns','0')]:
 old='\tif (nvram_invmatch("'+role+'_enable", "1") || get_ap_mode())\n\t\treturn '+result+';'
 guard='\n\n\tif (nvram_get_int("'+role+'_type") != 3) {\n'
 guard+='\t\tlogmessage('+role.upper()+'_LOG_NAME, "Legacy VPN protocol excluded from this build");\n'
 guard+='\t\treturn 1;\n\t}'
 changes['rc/vpn_'+('client' if role=='vpnc' else 'server')+'.c']=[(old,old+guard)]
changes['rc/vpn_server.c'].append(
 ('reapply_vpn_server(void)\n{\n\tint i_type;',
  'reapply_vpn_server(void)\n{\n\tint i_type;\n'
  '\tif (nvram_get_int("vpns_type") != 3) return;'))
changes['rc/net_ppp.c']=[
 ('\tif (wan_proto == IPV4_WAN_PROTO_PPTP) {',
  '\tif (wan_proto == IPV4_WAN_PROTO_PPTP || wan_proto == IPV4_WAN_PROTO_L2TP) {\n'
  '\t\tlogmessage("WAN", "PPTP/L2TP excluded; select a supported uplink");\n'
  '\t\treturn -1;\n\t}\n\n\tif (wan_proto == IPV4_WAN_PROTO_PPTP) {')]
pending=[]
for name,replacements in changes.items():
 path=root/name;text=path.read_text()
 for old,new in replacements:
  if text.count(old)!=1:raise SystemExit('VPN pruning anchor changed: '+name)
  text=text.replace(old,new,1)
 pending.append((path,text))
# Strip protocol choices only inside their exact select, not unrelated numeric values.
for page,field,removed in [('vpncli.asp','vpnc_type',('0','1','2')),
                           ('vpnsrv.asp','vpns_type',('0','1','2')),
                           ('Advanced_WAN_Content.asp','wan_proto',('pptp','l2tp'))]:
 path=root/'www/n56u_ribbon_fixed'/page;text=path.read_text()
 pattern=r'(<select\b[^>]*\bname="'+field+r'"[^>]*>)(.*?)(</select>)'
 matches=list(re.finditer(pattern,text,re.S))
 if len(matches)!=1:raise SystemExit('VPN protocol select changed: '+page)
 match=matches[0];body=match.group(2)
 values_to_remove=removed
 if field in ('vpnc_type','vpns_type'):
  # prepare-web.py may already have removed PPTP/L2TP from these pages.
  # Accept that prior transformation, but require and remove OpenVPN here.
  body=remove_unavailable_vpn_types(body,field,allow_legacy_missing=True)
  values_to_remove=()
 for value in values_to_remove:
  body,count=re.subn(r'^[ \t]*<option value="'+value+r'"[^\n]*</option>\n','',body,flags=re.M)
  if count!=1:raise SystemExit('VPN protocol option changed: '+page+' '+value)
 text=text[:match.start(2)]+body+text[match.end(2):]
 if field in ('vpnc_type','vpns_type'):
  old='document.form.'+field+'.remove(2);'
  if text.count(old)!=1:raise SystemExit('VPN index removal changed: '+page)
  text=text.replace(old,'$j("#'+field+' option[value=\'2\']").remove();')
  select_end=text.find('</select>',match.start())+len('</select>')
  text=text[:select_end]+'<p class="help-block"><#WRVPNExplicitType#></p>'+text[select_end:]
  # No implicit conversion of a saved legacy type to the first retained option.
  initial='function initial(){'
  valid='var mode = document.form.'+field+'.value;'
  if text.count(initial)!=1 or text.count('function validForm(){')!=1:
   raise SystemExit('VPN form functions changed: '+page)
  text=text.replace(initial,initial+'\n\tif ("<% nvram_get_x("", "'+field+'"); %>" != "3")\n'
   '\t\tdocument.form.'+field+'.selectedIndex = -1;',1)
  # Scope validation edit to validForm, not similarly named mode variables elsewhere.
  offset=text.index('function validForm(){');pos=text.find(valid,offset)
  if pos<0:raise SystemExit('VPN validation mode changed: '+page)
  end=pos+len(valid)
  text=(text[:end]+'\n\tif (mode != "3") {\n'
        +'\t\tdocument.form.'+field+'.focus();\n\t\treturn false;\n\t}'+text[end:])
 else:
  initial='function initial(){'
  valid='var wan_proto = document.form.wan_proto.value;'
  if text.count(initial)!=1 or text.count(valid)!=1:raise SystemExit('WAN form anchors changed')
  text=text.replace(initial,initial+'\n\tvar wr_saved_proto = "<% nvram_get_x("", "wan_proto"); %>";\n'
   '\tif (wr_saved_proto == "pptp" || wr_saved_proto == "l2tp")\n'
   '\t\tdocument.form.wan_proto.selectedIndex = -1;',1)
  text=text.replace(valid,valid+'\n\tif (wan_proto != "dhcp" && wan_proto != "static" && wan_proto != "pppoe") {\n'
   '\t\tdocument.form.wan_proto.focus();\n\t\treturn false;\n\t}',1)
  # Locate the exact select again after JS edits shifted offsets.
  selected=re.search(pattern,text,re.S)
  end=selected.end()
  text=text[:end]+'<p class="help-block"><#WRWANExplicitType#></p>'+text[end:]
 pending.append((path,text))
for name,note in [
 ('EN.footer','PPTP, L2TP and OpenVPN are excluded. Select the supported tunnel explicitly before enabling it. Saved legacy settings are not automatically converted.'),
 ('UK.dict','PPTP, L2TP та OpenVPN виключені. Перед увімкненням явно виберіть підтримуваний тунель. Старі налаштування автоматично не перетворюються.'),
 ('RU.dict','PPTP, L2TP и OpenVPN исключены. Перед включением явно выберите поддерживаемый туннель. Старые настройки автоматически не преобразуются.')]:
 path=root/'www/dict'/name;text=path.read_text()
 if 'WRVPNExplicitType=' in text:raise SystemExit('VPN migration label already exists')
 wan_note={'EN.footer':'PPTP/L2TP uplinks are excluded. Select DHCP, static IP or PPPoE explicitly. Opening this page does not convert saved settings.',
 'UK.dict':'WAN через PPTP/L2TP виключено. Явно виберіть DHCP, статичну IP-адресу або PPPoE. Відкриття сторінки не перетворює збережені налаштування.',
 'RU.dict':'WAN через PPTP/L2TP исключён. Явно выберите DHCP, статический IP или PPPoE. Открытие страницы не преобразует сохранённые настройки.'}[name]
 pending.append((path,text.rstrip()+'\nWRVPNExplicitType='+note+'\nWRWANExplicitType='+wan_note+'\n'))
for path,text in pending:path.write_text(text,encoding='utf-8',newline='\n')
print('Excluded poptop/xl2tpd and PPTP/L2TP PPP plugins; retained PPPoE/shared dependencies')
