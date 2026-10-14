#!/usr/bin/env python3
"""Install WR homepage device observations without replacing the network map."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
local=Path(__file__).resolve().parent;root=a.source/'trunk/user/www/n56u_ribbon_fixed';f=root/'index.asp';s=f.read_text(encoding='utf-8')
anchor='                <!--Body content-->'
if s.count(anchor)!=1 or s.count('</head>')!=1 or 'wr-connected-devices' in s:raise SystemExit('Homepage anchors changed; no files written')
assets={'wr-device-classify.js':'classify.js','wr-device-refresh.js':'refresh.js','wr-device-homepage.js':'homepage.js','wr-device-roaming.js':'roaming.js','wr-device-roaming-view.js':'roaming-view.js','wr-device-rssi.js':'rssi.js','wr-device-rssi-view.js':'rssi-view.js','wr-device-boot.js':'boot.js','wr-device-homepage.css':'homepage.css'}
includes='<link rel="stylesheet" href="/wr-device-homepage.css">\n'+''.join('<script src="/'+name+'"></script>\n' for name in assets if name.endswith('.js'))
s=s.replace('</head>',includes+'</head>',1)
keys=['state-current','state-stale','state-unavailable','state-updating','state-paused','state-stopped','last-observations','source-networkmap','source-radio','source-initialization']
translations={
 'EN.footer':['Current','Stale','Unavailable','Updating','Paused','Stopped','showing last available observations','Device observation source unavailable','Wi-Fi observation source unavailable','Observation initialization failed'],
 'UK.dict':['Актуальні дані','Застарілі дані','Недоступно','Оновлення','Призупинено','Зупинено','показано останні доступні спостереження','Джерело даних про пристрої недоступне','Джерело спостережень Wi-Fi недоступне','Не вдалося ініціалізувати спостереження'],
 'RU.dict':['Актуальные данные','Устаревшие данные','Недоступно','Обновление','Приостановлено','Остановлено','показаны последние доступные наблюдения','Источник данных об устройствах недоступен','Источник наблюдений Wi-Fi недоступен','Не удалось инициализировать наблюдения'],
}
dictionary_changes=[]
for name,values in translations.items():
    path=a.source/'trunk/user/www/dict'/name
    content=path.read_text(encoding='utf-8')
    if 'WRDeviceStatus_state-current=' in content:raise SystemExit('Device status labels already installed')
    dictionary_changes.append((path,content.rstrip('\n')+'\n'+'\n'.join('WRDeviceStatus_'+key+'='+value for key,value in zip(keys,values))+'\n'))
attributes=''.join(' data-wr-'+key+'="<#WRDeviceStatus_'+key+'#>"' for key in keys)
s=s.replace(anchor,anchor+'\n                <section id="wr-connected-devices" class="well" aria-label="Connected devices"'+attributes+'></section>\n                <section id="wr-roaming-history" class="well" aria-label="Wi-Fi history"></section>\n                <section id="wr-rssi-history" class="well" aria-label="RSSI history"></section>',1)
for name,source in assets.items():(root/name).write_bytes((local/source).read_bytes())
f.write_text(s,encoding='utf-8')
for path,content in dictionary_changes:path.write_text(content,encoding='utf-8')
print('Installed homepage observations with classification and automatic refresh; existing network map preserved')
