#!/usr/bin/env python3
"""Install WR homepage device observations without replacing the network map."""
import argparse
import json
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
extra_keys=['title','description','retry','source-time-unavailable','empty','no-match','source-time']
extra_labels={
 'EN.footer':['Connected devices','Passive observations; current connection and network role may be unknown.','Refresh','Source update time unavailable','No observations available','No devices match this category','Source updated'],
 'UK.dict':['Підключені пристрої','Пасивні спостереження; поточне підключення та роль у мережі можуть бути невідомими.','Оновити','Час оновлення джерела недоступний','Немає доступних спостережень','Немає пристроїв цієї категорії','Джерело оновлено'],
 'RU.dict':['Подключённые устройства','Пассивные наблюдения; текущее подключение и роль в сети могут быть неизвестны.','Обновить','Время обновления источника недоступно','Нет доступных наблюдений','Нет устройств этой категории','Источник обновлён'],
}
keys+=extra_keys
for name in translations:translations[name]+=extra_labels[name]
table_keys=['column-device','column-connection','column-category','column-confidence','connection-associated','connection-last','connection-seen','connection-unknown','confidence-unknown','confidence-possible','confidence-high','confidence-manufacturer','confidence-user','unnamed','classification-none','last-evidence']
table_labels={
 'EN.footer':['Device / address','Connection evidence','Category','Confidence','Wi-Fi association','Last known observation','Seen by networkmap','Connection unknown','Unknown','Possible','High','Manufacturer identified','User specified','Unnamed device','No reliable classification evidence','Last available evidence'],
 'UK.dict':['Пристрій / адреса','Ознаки підключення','Категорія','Достовірність','Асоціація Wi-Fi','Останнє відоме спостереження','Помічено в networkmap','Підключення невідоме','Невідомо','Можливо','Висока','Виробника визначено','Задано користувачем','Пристрій без назви','Немає надійних ознак для класифікації','Останні доступні ознаки'],
 'RU.dict':['Устройство / адрес','Признаки подключения','Категория','Достоверность','Ассоциация Wi-Fi','Последнее известное наблюдение','Замечено в networkmap','Подключение неизвестно','Неизвестно','Возможно','Высокая','Производитель определён','Задано пользователем','Устройство без имени','Нет надёжных признаков для классификации','Последние доступные признаки'],
}
keys+=table_keys
for name in translations:translations[name]+=table_labels[name]
detail_keys=['network-primary','network-guest','network-iot','network-unknown','category-all','category-unknown','category-tv','notice-truncated','notice-invalid','evidence-android-host','evidence-android-dhcp','evidence-windows-host','evidence-windows-dhcp','evidence-tv-host','evidence-conflict','evidence-manual','evidence-manufacturer']
detail_labels={
 'EN.footer':['Primary network','Guest network','IoT network','Network not identified','All','Unknown','Smart TV','Snapshot truncated to bounded source limits','Invalid source records','Hostname suggests Android','DHCP vendor class suggests Android','Hostname suggests Windows','DHCP vendor class suggests Windows','Hostname suggests a television','Conflicting OS clues','Manual user correction','Local OUI manufacturer'],
 'UK.dict':['Основна мережа','Гостьова мережа','Мережа IoT','Мережу не визначено','Усі','Невідомо','Смарттелевізор','Знімок скорочено до встановлених обмежень джерела','Некоректні записи джерела','Назва пристрою вказує на Android','Клас постачальника DHCP вказує на Android','Назва пристрою вказує на Windows','Клас постачальника DHCP вказує на Windows','Назва пристрою вказує на телевізор','Суперечливі ознаки ОС','Ручне уточнення користувачем','Виробник за локальним OUI'],
 'RU.dict':['Основная сеть','Гостевая сеть','Сеть IoT','Сеть не определена','Все','Неизвестно','Смарттелевизор','Снимок сокращён до установленных ограничений источника','Некорректные записи источника','Имя устройства указывает на Android','Класс поставщика DHCP указывает на Android','Имя устройства указывает на Windows','Класс поставщика DHCP указывает на Windows','Имя устройства указывает на телевизор','Противоречивые признаки ОС','Ручное уточнение пользователем','Производитель по локальному OUI'],
}
keys+=detail_keys
for name in translations:translations[name]+=detail_labels[name]
rssi_labels=json.loads((local/'rssi-labels.json').read_text(encoding='utf-8'))
keys+=list(rssi_labels)
for column,name in enumerate(('EN.footer','UK.dict','RU.dict')):
    translations[name]+=[values[column] for values in rssi_labels.values()]
history_labels=json.loads((local/'history-labels.json').read_text(encoding='utf-8'))
keys+=list(history_labels)
for column,name in enumerate(('EN.footer','UK.dict','RU.dict')):
    translations[name]+=[values[column] for values in history_labels.values()]
for name,values in translations.items():
    if len(values)!=len(keys):raise SystemExit('Device translation count mismatch: '+name)
    path=a.source/'trunk/user/www/dict'/name
    content=path.read_text(encoding='utf-8')
    if 'WRDeviceStatus_state-current=' in content:raise SystemExit('Device status labels already installed')
    dictionary_changes.append((path,content.rstrip('\n')+'\n'+'\n'.join('WRDeviceStatus_'+key+'='+value for key,value in zip(keys,values))+'\n'))
attributes=''.join(' data-wr-'+key+'="<#WRDeviceStatus_'+key+'#>"' for key in keys)
state_attributes=''.join(' data-wr-'+key+'="<#WRDeviceStatus_'+key+'#>"' for key in keys[:7])
rssi_attributes=''.join(' data-wr-'+key+'="<#WRDeviceStatus_'+key+'#>"' for key in rssi_labels)
history_attributes=''.join(' data-wr-'+key+'="<#WRDeviceStatus_'+key+'#>"' for key in history_labels)
s=s.replace(anchor,anchor+'\n                <section id="wr-connected-devices" class="well" aria-label="Connected devices"'+attributes+'></section>\n                <section id="wr-roaming-history" class="well" aria-label="Wi-Fi history"'+state_attributes+history_attributes+'></section>\n                <section id="wr-rssi-history" class="well" aria-label="RSSI history"'+state_attributes+rssi_attributes+'></section>',1)
for name,source in assets.items():(root/name).write_bytes((local/source).read_bytes())
f.write_text(s,encoding='utf-8')
for path,content in dictionary_changes:path.write_text(content,encoding='utf-8')
print('Installed homepage observations with classification and automatic refresh; existing network map preserved')
