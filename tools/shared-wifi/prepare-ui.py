#!/usr/bin/env python3
"""Add explicit shared main-network controls to both existing Wi-Fi pages."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
root=a.source/'trunk/user/www';changes=[]
for band,name in [('rt','Advanced_Wireless2g_Content.asp'),('wl','Advanced_Wireless_Content.asp')]:
 f=root/'n56u_ribbon_fixed'/name;s=f.read_text(encoding='utf-8')
 script='<script type="text/javascript" src="/jquery.js"></script>'
 marker='name="'+band+'_ssid"'
 if s.count(script)!=1 or s.count(marker)!=1 or 'data-wr-shared-choice' in s or s.count('\t\tshowLoading();')!=1: raise ValueError('Shared Wi-Fi page anchors changed; no files written')
 end=s.index('</tr>',s.index(marker))+len('</tr>')
 row='''<tr><th><#WR_WIFI_SHARED_Label#></th><td>
<select data-wr-shared-choice data-current="<% nvram_get_x("", "wr_wifi_shared"); %>" data-error="<#WR_WIFI_SHARED_Error#>">
<option value="0" <% nvram_match_x("", "wr_wifi_shared", "0", "selected"); %>><#WR_WIFI_SHARED_Off#></option>
<option value="1" <% nvram_match_x("", "wr_wifi_shared", "1", "selected"); %>><#WR_WIFI_SHARED_On#></option>
</select>
<input type="hidden" name="wr_wifi_shared" value="0" disabled>
<input type="hidden" name="wr_wifi_source" value="'''+band+'''" disabled>
<p><#WR_WIFI_SHARED_Note#></p><p><#WR_WIFI_SHARED_Keep#></p>
</td></tr>'''
 s=s[:end]+'\n'+row+s[end:]
 s=s.replace(script,script+'\n<script type="text/javascript" src="/shared-wifi.js"></script>')
 s=s.replace('\t\tshowLoading();','\t\tif (!WRSharedWifi.prepare(document.form, "'+band+'")) return;\n\t\tshowLoading();')
 changes.append((f,s))
labels={
 'EN.footer':('Shared 2.4 / 5 GHz main network','Independent','Shared','Enabling copies the SSID, security and password from this page to the other band. Channels, widths, schedules and guest networks remain separate.','Disabling keeps the current credentials of both bands. Apply saves changes.','Shared mode requires a valid SSID and open security without WEP, or WPA Personal with a valid password.'),
 'UK.dict':('Спільна основна мережа 2,4 / 5 ГГц','Окремі налаштування','Спільні налаштування','Увімкнення переносить SSID, захист і пароль із цієї сторінки на другий діапазон. Канали, ширина, розклади та гостьові мережі залишаються окремими.','Вимкнення зберігає поточні дані обох діапазонів. Зміни зберігаються кнопкою «Застосувати».','Для спільного режиму потрібні коректний SSID і відкрита мережа без WEP або WPA Personal з коректним паролем.'),
 'RU.dict':('Общая основная сеть 2,4 / 5 ГГц','Раздельные настройки','Общие настройки','Включение переносит SSID, защиту и пароль с этой страницы на второй диапазон. Каналы, ширина, расписания и гостевые сети остаются раздельными.','Выключение сохраняет текущие данные обоих диапазонов. Изменения сохраняются кнопкой «Применить».','Общий режим требует корректного SSID и открытой сети без WEP либо WPA Personal с корректным паролем.')}
for name,values in labels.items():
 f=root/'dict'/name;s=f.read_text(encoding='utf-8')
 if 'WR_WIFI_SHARED_' in s: raise ValueError('Shared labels already installed')
 s=s.rstrip('\n')+'\n'+''.join('WR_WIFI_SHARED_'+key+'='+value+'\n' for key,value in zip(('Label','Off','On','Note','Keep','Error'),values));changes.append((f,s))
f=root/'n56u_ribbon_fixed/shared-wifi.js'
if f.exists(): raise ValueError('Shared UI asset already exists')
changes.append((f,(Path(__file__).parent/'ui.js').read_text(encoding='utf-8')))
for f,s in changes:f.write_text(s,encoding='utf-8')
print('Added shared Wi-Fi controls to both main network pages')
