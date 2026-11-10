#!/usr/bin/env python3
"""Install the read-only Modern WebUI shell and live JSON route into a source tree."""
import argparse
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
a=p.parse_args()
here=Path(__file__).resolve().parent
root=a.source.resolve(strict=True)
httpd=root/'trunk/user/httpd'
web_ex=httpd/'web_ex.c'
www=root/'trunk/user/www'
target=www/'modern'
shared=here.parent/'shared-wifi/ui.js'

if not web_ex.is_file() or not www.is_dir() or not shared.is_file():
 p.error('not a prepared Padavan source tree')
if target.exists():
 p.error('Modern target already exists; refusing to overwrite')

source=web_ex.read_text(encoding='utf-8')
anchor='struct mime_handler mime_handlers[] = {\n'
if source.count(anchor)!=1:
 p.error('mime handler anchor changed')
if 'do_wr_modern_json' in source:
 p.error('Modern JSON route already present')

hook=(here/'wr-modern-http.inc').read_text(encoding='utf-8')
static_routes={
 'index.html':'text/html', 'app.js':'text/javascript',
 'wifi.js':'text/javascript', 'shared-wifi.js':'text/javascript',
 'wifi-schema.json':'application/json', 'styles.css':'text/css',
 'favicon.svg':'image/svg+xml',
}
route=('#if defined(BOARD_WR1200JS)\n'
       '\t{ "wr_modern.json", "application/json", no_cache_IE, NULL, do_wr_modern_json, 1 },\n')
for name,mime in static_routes.items():
 route+=f'\t{{ "modern/{name}", "{mime}", no_cache_IE, NULL, do_file, 1 }},\n'
route+='#endif\n'
# Prepare and validate every input before changing the source tree.
assets={name:(here/'public'/name).read_bytes()
        for name in ('styles.css','favicon.svg')}
assets['shared-wifi.js']=shared.read_bytes()

index=(here/'public/index.html').read_text(encoding='utf-8')
index=index.replace('<title>Padavan Modern — локальний перегляд</title>',
                    '<title>Padavan Modern — WR1200JS</title>')
index=index.replace('ЛОКАЛЬНЕ DEMO · дані та служби на цій сторінці не є станом роутера',
                    'PADAVAN MODERN · LIVE READ-ONLY')
index=index.replace('Локальний макет усіх погоджених розділів. Дані позначені DEMO; налаштування не передаються роутеру.',
                    'Padavan Modern read-only: відображення стану не змінює конфігурацію роутера.')
index=index.replace('Демонстраційний стан мереж','Поточний стан мереж')
index=index.replace('Демонстраційний графік трафіку WAN','Графік трафіку WAN')
index=index.replace('<span class="demo-chip">DEMO</span>','<span class="demo-chip">LIVE</span>')
index=index.replace('Недоступно в локальному DEMO','Керування доступне у Padavan Classic')
index=index.replace('Увімкнено (макет)','Н/Д')
index=index.replace('Цей preview не запускає роутерний ASP/CGI і не звертається до роутера.',
                    'Керування виконується у Padavan Classic; Modern не виконує ASP/CGI.')
index=index.replace('href="/modern/"','href="/modern/index.html"')
index=index.replace('href="/modern/#','href="/modern/index.html#')
for asset in ('favicon.svg','styles.css','app.js','shared-wifi.js','wifi.js'):
 index=index.replace(f'/{asset}',f'/modern/{asset}')
assets['index.html']=index.encode('utf-8')

app=(here/'public/app.js').read_text(encoding='utf-8')
old='fetch("/api/dashboard.json", { method: "GET", credentials: "omit", cache: "no-store" })'
new='fetch("/wr_modern.json", { method: "GET", credentials: "same-origin", cache: "no-store" })'
if app.count(old)!=1:
 p.error('dashboard fetch anchor changed')
assets['app.js']=app.replace(old,new,1).encode('utf-8')

wifi=(here/'public/wifi.js').read_text(encoding='utf-8')
if wifi.count("fetch('/wifi-schema.json', {credentials:'omit', cache:'no-store'})")!=1:
 p.error('wifi schema anchor changed')
wifi=wifi.replace("fetch('/wifi-schema.json', {credentials:'omit', cache:'no-store'})",
                  "fetch('/modern/wifi-schema.json', {credentials:'same-origin', cache:'no-store'})",1)
assets['wifi.js']=wifi.encode('utf-8')

schema=(here/'public/wifi-schema.json').read_text(encoding='utf-8')
if schema.count('"demo": true')!=1:
 p.error('wifi schema demo marker changed')
assets['wifi-schema.json']=schema.replace('"demo": true','"demo": false',1).encode('utf-8')

target.mkdir()
for name,data in assets.items():
 (target/name).write_bytes(data)
web_ex.write_text(hook+'\n'+source.replace(anchor,anchor+route,1),encoding='utf-8')
print('Installed /modern/index.html and authenticated /wr_modern.json; Classic assets untouched')
