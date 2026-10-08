#!/usr/bin/env python3
"""Add explicitly unsaved local QR previews to the two main Wi-Fi pages."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
a=p.parse_args()
root=a.source/'trunk/user/www'
changes=[]
script='<script type="text/javascript" src="/jquery.js"></script>'
for band,name in [('rt','Advanced_Wireless2g_Content.asp'),('wl','Advanced_Wireless_Content.asp')]:
 f=root/'n56u_ribbon_fixed'/name
 s=f.read_text(encoding='utf-8')
 marker='name="'+band+'_ssid"'
 if s.count(script)!=1 or s.count(marker)!=1 or 'wr_wifi_qr' in s:
  raise ValueError('QR page anchors changed; no files written')
 end=s.index('</tr>',s.index(marker))+len('</tr>')
 row='<tr><td colspan="2"><button type="button" class="btn" onclick="wrWifiQrShow(\''+band+'\')"><#WR_WIFI_QR_Show#></button> '
 row+='<button type="button" class="btn" onclick="wrWifiQrHide()"><#WR_WIFI_QR_Hide#></button>'
 row+='<p id="wr_wifi_qr_message" data-error="<#WR_WIFI_QR_Error#>" data-preview="<#WR_WIFI_QR_Preview#>"></p>'
 row+='<div id="wr_wifi_qr" style="display:none;background:white;padding:16px"></div></td></tr>'
 s=s[:end]+'\n'+row+s[end:]
 tags='\n'.join('<script type="text/javascript" src="/'+asset+'"></script>' for asset in ('wifi-qrcode-renderer.js','wifi-qr-payload.js','wifi-qr-preview.js'))
 s=s.replace(script,script+'\n'+tags)
 changes.append((f,s))
labels={
 'EN.footer':('Show Wi-Fi QR preview','Hide QR','Unsupported security or invalid Wi-Fi fields.','Unsaved preview of current form fields. Applying settings is separate. The QR contains your password.'),
 'UK.dict':('Показати QR Wi-Fi','Приховати QR','Непідтримуваний захист або некоректні поля Wi-Fi.','Незбережений перегляд поточних полів форми. Налаштування застосовуються окремо. QR містить пароль.'),
 'RU.dict':('Показать QR Wi-Fi','Скрыть QR','Неподдерживаемая защита или неверные поля Wi-Fi.','Несохранённый просмотр текущих полей формы. Настройки применяются отдельно. QR содержит пароль.')}
for name,values in labels.items():
 f=root/'dict'/name;s=f.read_text(encoding='utf-8')
 if 'WR_WIFI_QR_' in s: raise ValueError('QR labels already present; no files written')
 s=s.rstrip('\n')+'\n'+''.join('WR_WIFI_QR_'+key+'='+value+'\n' for key,value in zip(('Show','Hide','Error','Preview'),values))
 changes.append((f,s))
for asset in ('wifi-qrcode-renderer.js','wifi-qr-payload.js','wifi-qr-preview.js'):
 target=root/'n56u_ribbon_fixed'/asset
 if target.exists(): raise ValueError('QR asset already installed; no files written')
 changes.append((target,(Path(__file__).parent/asset).read_text(encoding='utf-8')))
for f,s in changes: f.write_text(s,encoding='utf-8')
print('Added local, unsaved Wi-Fi QR previews for both main networks')
