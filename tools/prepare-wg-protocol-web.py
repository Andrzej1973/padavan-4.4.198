#!/usr/bin/env python3
"""Expose per-role WireGuard/AmneziaWG selection through existing VPN Apply events."""
import argparse
from pathlib import Path
import re
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path)
a=p.parse_args();root=a.source/'trunk/user';changes={}
awg_fields=['Jc','Jmin','Jmax','S1','S2','H1','H2','H3','H4']
for name in ['shared/defaults.c','httpd/variables.c']:
 text=(root/name).read_text()
 for role,event in [('vpnc','VPNCLI'),('vpns','VPNSVR')]:
  if name=='shared/defaults.c':
   old='\t{ "'+role+'_type", "0" },'
   new=old+'\n\t{ "'+role+'_wg_protocol", "" },'
  else:
   old='\t\t\t{"'+role+'_type", "", NULL, EVM_RESTART_'+event+'},'
   new=old+'\n\t\t\t{"'+role+'_wg_protocol", "", NULL, EVM_RESTART_'+event+'},'
  if role=='vpns':
   for key in awg_fields:
    field='vpns_awg_'+key.lower()
    if name=='shared/defaults.c':new+='\n\t{ "'+field+'", "" },'
    else:new+='\n\t\t\t{"'+field+'", "", NULL, EVM_RESTART_VPNSVR},'
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
 if role=='vpns':
  select=select.replace('change_vpns_type();','change_vpns_type();wrAWGServerVisibility();')
  select+='<fieldset id="wr_awg_server_fields"><legend>AmneziaWG</legend><p><#WRWGServerOptions#></p>'
  for key in awg_fields:
   field='vpns_awg_'+key.lower()
   select+='<label>'+key+' <input name="'+field+'" inputmode="numeric" pattern="[0-9]*" maxlength="10" value="<% nvram_get_x("", "'+field+'"); %>"></label>'
  select+='</fieldset>'

 text=text[:match.end()]+select+text[match.end():]
 old=".html('AmneziaWG');"
 if text.count(old)!=1:raise SystemExit('Protocol title anchor changed')
 text=text.replace(old,".html('WireGuard / AmneziaWG');")
 if role=='vpnc':
  old="showhide_div('tbl_vpnc_amnezia', found_app_awg() && is_wg);"
  if text.count(old)!=1:raise SystemExit('AWG panel capability anchor changed')
  text=text.replace(old,"showhide_div('tbl_vpnc_amnezia', found_app_awg() && is_wg && document.form.vpnc_wg_protocol.value != 'wireguard');")
 if role=='vpns':
  code="""function wrAWGServerVisibility(){var active=found_app_awg() && document.form.vpns_wg_protocol.value!='wireguard';showhide_div('wr_awg_server_fields',active);var fields=document.getElementById('wr_awg_server_fields').getElementsByTagName('input');for(var i=0;i<fields.length;i++)fields[i].disabled=!active;}
function wrValidateAwgServer(){
 var ranges={jc:[1,128],jmin:[0,1279],jmax:[1,1280],s1:[0,1132],s2:[0,1188],h1:[0,4294967295],h2:[0,4294967295],h3:[0,4294967295],h4:[0,4294967295]},values={};
 for(var key in ranges){if(!ranges.hasOwnProperty(key))continue;var field=document.form['vpns_awg_'+key],value=field.value;if(value===''){values[key]='';continue;}if(!/^\\d+$/.test(value)||Number(value)<ranges[key][0]||Number(value)>ranges[key][1]){alert('<#WRWGServerInvalid#>');field.focus();field.select();return false;}values[key]=Number(value);}
 if((values.jmin==='')!==(values.jmax==='')||(values.jmin!==''&&values.jmax<=values.jmin)){alert('<#WRWGServerInvalid#>');return false;}
 if(values.s1!==''&&values.s2!==''&&values.s1+56===values.s2){alert('<#WRWGServerInvalid#>');return false;}
 var headers=[];for(var i=1;i<=4;i++){var value=values['h'+i];if(value==='')continue;if(headers.indexOf(value)!==-1){alert('<#WRWGServerInvalid#>');return false;}headers.push(value);}
 return true;
}
document.addEventListener('DOMContentLoaded',wrAWGServerVisibility);
"""
  text=text.replace('function initial(){',code+'function initial(){',1)
  anchor='if(!valid_vpn_subnet(document.form.vpns_vnet))\n\t\t\treturn false;'
  if text.count(anchor)!=1:raise SystemExit('Server WireGuard validation anchor changed')
  text=text.replace(anchor,anchor+"\n\t\tif (document.form.vpns_wg_protocol.value != 'wireguard' && found_app_awg() && !wrValidateAwgServer())\n\t\t\treturn false;",1)
 else:
  old='if (found_app_awg()) {\n\t\t\tif(!validate_range(document.form.vpnc_awg_jc'
  if text.count(old)!=1:raise SystemExit('Client AWG validation anchor changed')
  text=text.replace(old,"if (found_app_awg() && document.form.vpnc_wg_protocol.value != 'wireguard') {\n\t\t\tif(!validate_range(document.form.vpnc_awg_jc")
 changes[path]=text
for name,title,compat,note in [
 ('EN.footer','Tunnel protocol','Previous automatic selection','Select the protocol for this client or server profile. The setting does not prove an active tunnel. WG and AWG share this profile; changing protocol restarts it. Empty preserves the previous automatic choice.'),
 ('UK.dict','Протокол тунелю','Попередній автоматичний вибір','Виберіть протокол цього профілю клієнта або сервера. Налаштування не підтверджує активний тунель. WG та AWG використовують спільний профіль; зміна протоколу перезапускає його. Порожнє значення зберігає попередній автоматичний вибір.'),
 ('RU.dict','Протокол туннеля','Прежний автоматический выбор','Выберите протокол этого профиля клиента или сервера. Настройка не подтверждает активный туннель. WG и AWG используют общий профиль; смена протокола перезапускает его. Пустое значение сохраняет прежний автоматический выбор.')]:
 path=root/'www/dict'/name;text=path.read_text()
 if 'WRWGProtocol=' in text:raise SystemExit('Protocol labels already installed')
 server_note={'EN.footer':'Optional AWG values; blank uses module defaults. Jc 1–128; Jmin/Jmax 0–1279/1–1280 with Jmax greater; S1/S2 0–1132/0–1188 and S1+56 must differ from S2; H1–H4 0–4294967295 and unique. Exported client file and QR use the same values. Ignored for standard WireGuard.',
 'UK.dict':'Необов’язкові параметри AWG; порожнє поле використовує типові значення модуля. Jc 1–128; Jmin/Jmax 0–1279/1–1280, Jmax має бути більшим; S1/S2 0–1132/0–1188, S1+56 не має дорівнювати S2; H1–H4 0–4294967295, значення унікальні. Файл клієнта й QR містять ті самі значення. Для звичайного WireGuard не застосовуються.',
 'RU.dict':'Необязательные параметры AWG; пустое поле использует значения модуля по умолчанию. Jc 1–128; Jmin/Jmax 0–1279/1–1280, Jmax должен быть больше; S1/S2 0–1132/0–1188, S1+56 не должен равняться S2; H1–H4 0–4294967295, значения уникальны. Файл клиента и QR содержат те же значения. Для обычного WireGuard не применяются.'}[name]
 invalid={'EN.footer':'Invalid AmneziaWG values. Check Jc, paired Jmin/Jmax, S1/S2 relation, and unique H1–H4 values.',
 'UK.dict':'Некоректні параметри AmneziaWG. Перевірте Jc, пару Jmin/Jmax, співвідношення S1/S2 та унікальність H1–H4.',
 'RU.dict':'Некорректные параметры AmneziaWG. Проверьте Jc, пару Jmin/Jmax, соотношение S1/S2 и уникальность H1–H4.'}[name]
 changes[path]=text.rstrip()+'\nWRWGProtocol='+title+'\nWRWGCompatibility='+compat+'\nWRWGProtocolNote='+note+'\nWRWGServerOptions='+server_note+'\nWRWGServerInvalid='+invalid+'\n'
for path,text in changes.items():path.write_text(text,encoding='utf-8',newline='\n')
print('Prepared per-role WG/AWG protocol controls, compatibility defaults and existing Apply events')
