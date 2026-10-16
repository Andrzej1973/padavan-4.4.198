#!/usr/bin/env python3
"""Use the reviewed local UTF-8 QR renderer for WG/AWG client configuration exports."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path)
a=p.parse_args();root=a.source/'trunk/user/www';page=root/'n56u_ribbon_fixed/vpnsrv.asp';text=page.read_text()
old='<script type="text/javascript" src="/qrcode.min.js"></script>'
start='function export_client_wg(num){';end='function showACLList('
if text.count(old)!=1 or text.count(start)!=1 or text.count(end)!=1 or 'wrVPNQR' in text:raise SystemExit('VPN QR anchors changed')
text=text.replace(old,'<script type="text/javascript" src="/wifi-qrcode-renderer.js"></script>')
labels='var wrVPNQrLabels={changed:"<#WRVPNQRChanged#>",loading:"<#WRVPNQRLoading#>",error:"<#WRVPNQRError#>",private:"<#WRVPNQRPrivate#>"};\n'
i=text.index(start);j=text.index(end,i)
text=text[:i]+labels+Path(__file__).with_name('vpn-status').joinpath('qr-export.js').read_text()+'\n'+text[j:]
anchor='function initial(){'
if text.count(anchor)!=1:raise SystemExit('VPN initial anchor changed')
text=text.replace(anchor,anchor+'\n window.setTimeout(wrVPNQrCapture,0);',1)
anchor='<select name="vpns_type"'
i=text.index('</tr>',text.index(anchor))+len('</tr>')
text=text[:i]+'<tr><td colspan="2"><p id="wr_vpn_qr_message" role="status"></p><button type="button" class="btn" onclick="wrVPNQrReset();wrVPNQrMessage(\'\');"><#WRVPNQRHide#></button></td></tr>'+text[i:]
changes=[(page,text)]
for name,values in [
 ('EN.footer',['Apply settings and reload before exporting a changed profile.','Reading the saved client configuration…','QR unavailable: export failed, invalid configuration or QR capacity exceeded.','Private client configuration: the QR and file contain the private key. Hide after importing.','Hide VPN QR and configuration']),
 ('UK.dict',['Після зміни профілю застосуйте налаштування та перечитайте сторінку перед експортом.','Читання збереженої конфігурації клієнта…','QR недоступний: помилка експорту, некоректний конфіг або перевищено місткість QR.','Приватна конфігурація клієнта: QR і файл містять приватний ключ. Приховайте після імпорту.','Приховати VPN QR і конфігурацію']),
 ('RU.dict',['После изменения профиля примените настройки и перечитайте страницу перед экспортом.','Чтение сохранённой конфигурации клиента…','QR недоступен: ошибка экспорта, неверный конфиг или превышена ёмкость QR.','Приватная конфигурация клиента: QR и файл содержат приватный ключ. Скройте после импорта.','Скрыть VPN QR и конфигурацию'])]:
 path=root/'dict'/name;dictionary=path.read_text()
 if 'WRVPNQRChanged=' in dictionary:raise SystemExit('VPN QR labels already installed')
 changes.append((path,dictionary.rstrip()+'\n'+'\n'.join('WRVPNQR'+key+'='+value for key,value in zip(['Changed','Loading','Error','Private','Hide'],values))+'\n'))
# Wi-Fi QR preparation may already have installed this shared renderer earlier
# in the workflow. Reuse it when identical; reject a conflicting implementation.
renderer=root/'n56u_ribbon_fixed/wifi-qrcode-renderer.js'
expected_renderer=Path(__file__).with_name('wifi-qrcode-renderer.js').read_text()
if renderer.exists():
 if renderer.read_text(encoding='utf-8')!=expected_renderer:raise SystemExit('shared QR renderer differs; no files written')
else:changes.append((renderer,expected_renderer))
for path,text in changes:path.write_text(text,encoding='utf-8',newline='\n')
print('Prepared shared local UTF-8 VPN QR, exact download payload, stale response and private-data clearing')
