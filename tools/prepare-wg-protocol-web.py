#!/usr/bin/env python3
"""Expose per-role WireGuard/AmneziaWG selection through existing VPN Apply events."""
import argparse
from pathlib import Path
import re
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path)
a=p.parse_args();root=a.source/'trunk/user';changes={}
for name in ['shared/defaults.c','httpd/variables.c']:
 text=(root/name).read_text()
 for role,event in [('vpnc','VPNCLI'),('vpns','VPNSVR')]:
  if name=='shared/defaults.c':
   old='\t{ "'+role+'_type", "0" },'
   new=old+'\n\t{ "'+role+'_wg_protocol", "" },'
  else:
   old='\t\t\t{"'+role+'_type", "", NULL, EVM_RESTART_'+event+'},'
   new=old+'\n\t\t\t{"'+role+'_wg_protocol", "", NULL, EVM_RESTART_'+event+'},'
  if text.count(old)!=1 or role+'_wg_protocol' in text:raise SystemExit('Protocol setting anchor changed: '+name)
  text=text.replace(old,new,1)
 changes[root/name]=text
for page,role in [('vpncli.asp','vpnc'),('vpnsrv.asp','vpns')]:
 path=root/'www/n56u_ribbon_fixed'/page;text=path.read_text()
 pattern=r'<select\b[^>]*name="'+role+r'_type"[^>]*>.*?</select>'
 match=re.search(pattern,text,re.S)
 if not match or role+'_wg_protocol' in text:raise SystemExit('Protocol page anchor changed: '+page)
 field=role+'_wg_protocol'
 select='<label for="'+field+'"><#WRWGProtocol#></label><select name="'+field+'" id="'+field+'" onchange="change_'+role+'_type();">'
 for value,label in [('', '<#WRWGCompatibility#>'),('wireguard','WireGuard'),('amneziawg','AmneziaWG')]:
  select+='<option value="'+value+'" <% nvram_match_x("", "'+field+'", "'+value+'", "selected"); %>>'+label+'</option>'
 select+='</select><p class="help-block"><#WRWGProtocolNote#></p>'
 text=text[:match.end()]+select+text[match.end():]
 old=".html('AmneziaWG');"
 if text.count(old)!=1:raise SystemExit('Protocol title anchor changed')
 text=text.replace(old,".html('WireGuard / AmneziaWG');")
 if role=='vpnc':
  old="showhide_div('tbl_vpnc_amnezia', found_app_awg() && is_wg);"
  if text.count(old)!=1:raise SystemExit('AWG panel capability anchor changed')
  text=text.replace(old,"showhide_div('tbl_vpnc_amnezia', found_app_awg() && is_wg && document.form.vpnc_wg_protocol.value != 'wireguard');")
 changes[path]=text
for name,title,compat,note in [
 ('EN.footer','Tunnel protocol','Previous automatic selection','Select the protocol for this client or server profile. The setting does not prove an active tunnel. WG and AWG share this profile; changing protocol restarts it. Empty preserves the previous automatic choice.'),
 ('UK.dict','Протокол тунелю','Попередній автоматичний вибір','Виберіть протокол цього профілю клієнта або сервера. Налаштування не підтверджує активний тунель. WG та AWG використовують спільний профіль; зміна протоколу перезапускає його. Порожнє значення зберігає попередній автоматичний вибір.'),
 ('RU.dict','Протокол туннеля','Прежний автоматический выбор','Выберите протокол этого профиля клиента или сервера. Настройка не подтверждает активный туннель. WG и AWG используют общий профиль; смена протокола перезапускает его. Пустое значение сохраняет прежний автоматический выбор.')]:
 path=root/'www/dict'/name;text=path.read_text()
 if 'WRWGProtocol=' in text:raise SystemExit('Protocol labels already installed')
 changes[path]=text.rstrip()+'\nWRWGProtocol='+title+'\nWRWGCompatibility='+compat+'\nWRWGProtocolNote='+note+'\n'
for path,text in changes.items():path.write_text(text,encoding='utf-8',newline='\n')
print('Prepared per-role WG/AWG protocol controls, compatibility defaults and existing Apply events')
