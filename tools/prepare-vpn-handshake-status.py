#!/usr/bin/env python3
"""Install WR-only periodic handshake observations without request-time commands."""
import argparse
import re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
local=Path(__file__).resolve().parent/'vpn-status'
http=a.source/'trunk/user/httpd'
web=http/'web_ex.c';daemon=http/'httpd.c'
s=web.read_text(encoding='utf-8');d=daemon.read_text(encoding='utf-8')
anchor='struct ej_handler ej_handlers[] =\n'
entry='\t{ "wr_vpn_interface_state", ej_wr_vpn_interface_state},\n'
tick='\t\twr_device_background_tick();'
close='\twr_device_background_close();'
if any(text.count(value)!=1 for text,value in [(s,anchor),(s,entry),(d,tick),(d,close)]) or 'wr_vpn_background_tick' in d:
    raise SystemExit('VPN handshake integration anchors changed; no files written')
code=(local/'http-status.inc').read_text(encoding='utf-8')
s=s.replace(anchor,code+'\n'+anchor).replace(entry,entry+'#if defined(BOARD_WR1200JS)\n\t{ "wr_vpn_handshake_state", ej_wr_vpn_handshake_state},\n\t{ "wr_vpn_status", ej_wr_vpn_status},\n#endif\n')
d='#if defined(BOARD_WR1200JS)\nextern void wr_vpn_background_tick(void);\nextern void wr_vpn_background_close(void);\n#endif\n'+d
d=d.replace(tick,tick+'\n\t\twr_vpn_background_tick();').replace(close,close+'\n\twr_vpn_background_close();')
changes=[(web,s),(daemon,d)]
keys=['Unknown','Stale','Peers','Recent','Never','Old','Future','SampleAge','HandshakeAge','Seconds','Note','Refresh']
labels={
 'EN.footer':['Handshake data unavailable','Handshake data stale','Peers','Handshakes within 300 seconds at sampling','No handshake yet','Older handshakes','Timestamps ahead of router clock','Sample age','Youngest handshake age','seconds','Handshake observations refresh every 30 seconds while this page is visible. They do not prove working routes or Internet access.','Refresh status'],
 'UK.dict':['Дані handshake недоступні','Дані handshake застарілі','Вузли','Handshake за останні 300 секунд на момент збору','Ще без handshake','Давніші handshake','Час випереджає годинник роутера','Вік даних','Вік найсвіжішого handshake','с','Дані handshake оновлюються раз на 30 секунд, коли сторінка видима. Вони не підтверджують роботу маршрутів або доступ до інтернету.','Оновити стан'],
 'RU.dict':['Данные handshake недоступны','Данные handshake устарели','Узлы','Handshake за последние 300 секунд при сборе','Ещё без handshake','Более старые handshake','Время опережает часы роутера','Возраст данных','Возраст самого свежего handshake','с','Данные handshake обновляются раз в 30 секунд, пока страница видима. Они не подтверждают работу маршрутов или доступ к интернету.','Обновить состояние'],
}
ui=(local/'handshake-ui.js').read_text(encoding='utf-8')
for name,values in labels.items():
    path=a.source/'trunk/user/www/dict'/name
    content=path.read_text(encoding='utf-8')
    if 'WRHSUnknown=' in content:raise SystemExit('Handshake labels already present')
    changes.append((path,content.rstrip('\n')+'\n'+'\n'.join('WRHS'+k+'='+v for k,v in zip(keys,values))+'\n'))
for page,role in [('vpncli.asp','client'),('vpnsrv.asp','server')]:
    path=a.source/'trunk/user/www/n56u_ribbon_fixed'/page
    html=path.read_text(encoding='utf-8')
    anchor='<p class="help-block"><#WRVPNNote#></p>'
    if html.count(anchor)!=1 or len(re.findall(r'function initial\(\)\s*\{',html))!=1:
        raise SystemExit('Handshake page anchors changed: '+page)
    script=ui+'\nvar wrHSBusy=false;\nfunction wrHSRefresh(){\n'
    script+=' if(wrHSBusy || document.hidden)return;\n wrHSBusy=true;\n'
    script+=' var labels=['+','.join('"<#WRHS'+k+'#>"' for k in keys[:10])+'];\n'
    script+=' var interfaces=['+','.join('"<#WRVPN'+k+'#>"' for k in ['Off','Up','Missing','Unknown','StillUp','Down'])+'];\n'
    script+=' $j.ajax({url:"/update.cgi",data:{output:"wr_vpn_status",arg0:"'+role+'"},dataType:"json",cache:false,timeout:5000})\n'
    script+=' .done(function(o){$j("#wr_vpn_handshake_status").text(wrVPNHandshakeText(o && o.handshake,labels));$j("#wr_vpn_interface_status").text(o && typeof o.interface === "number" && interfaces[o.interface] || interfaces[3]);})\n'
    script+=' .fail(function(){$j("#wr_vpn_handshake_status").text(labels[0]);$j("#wr_vpn_interface_status").text(interfaces[3]);})\n'
    script+=' .always(function(){wrHSBusy=false;});\n}\n'
    html=re.sub(r'(function initial\(\)\s*\{)',lambda m:script+m[1]+'\n wrHSRefresh();\n window.setInterval(wrHSRefresh,30000);\n',html,count=1)
    html=html.replace(anchor,anchor+'<div id="wr_vpn_handshake_status" role="status"><#WRHSUnknown#></div><p class="help-block"><#WRHSNote#></p><button type="button" class="btn" onclick="wrHSRefresh()"><#WRHSRefresh#></button>')
    changes.append((path,html))
headers=http/'wr-vpn';headers.mkdir(exist_ok=True)
for name in ('handshake-observation.h','handshake-cache.h','handshake-worker.h','handshake-runtime.h'):
    (headers/name).write_bytes((local/name).read_bytes())
for path,content in changes:path.write_text(content,encoding='utf-8')
print('Installed WR handshake background sampling and EJ observation; peer keys are not exposed')
