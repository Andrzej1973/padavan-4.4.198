"""Inventory Classic controls for the isolated demo; never execute ASP or copy values."""
import hashlib
import json
import re
import html
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'artifacts-410/romfs-selected/www'
OUT = Path(__file__).resolve().parent / 'public/wifi-schema.json'
dictionary = dict(line.split('=', 1) for line in (SOURCE / 'UK.dict').read_text(encoding='utf-8').splitlines() if '=' in line)
dictionary.update({'APSTA_SSID':'SSID віддаленої точки', 'WIFILDPC2_itemname':'Кодування LDPC', 'WIFILDPC_itemname':'Кодування LDPC', 'WLANConfig11n_amsdu_itemname':'Увімкнути AMSDU', 'WLANConfig11n_80211kv':'Увімкнути 802.11k/v', 'WLANConfig11n_80211r':'Увімкнути 802.11r', 'WLANConfig11n_band_steering_itemname':'Band Steering', 'WLANConfig11n_mumimo_itemname':'MU-MIMO', 'WLANConfig11b_x_turbo_qam':'Turbo QAM', 'WLANConfig11b_x_rt_airtimefairness':'Розподіл ефірного часу'})

def label(text):
    text = re.sub(r'<#([^#]+)#>', lambda m: dictionary.get(m[1], m[1]), text)
    text = re.sub(r'<%.*?%>', '', text, flags=re.S)
    return html.unescape(' '.join(text.split()).strip(':? '))

class Controls(HTMLParser):
    def __init__(self):
        super().__init__(); self.fields = {}; self.current = None; self.option = None; self.heading = False; self.title = ''; self.in_script = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ('script', 'style'): self.in_script = True
        if tag == 'tr': self.title = ''
        if tag == 'th': self.heading = True
        if tag in ('input', 'select', 'textarea'):
            name = a.get('name', '')
            self.current = None
            if not name.startswith(('rt_', 'wl_')) or a.get('type') in ('hidden', 'button', 'submit'): return
            if name.endswith('_txbf') or name.endswith('_txbf_fake'): return
            field = self.fields.setdefault(name, {'key': name, 'label': label(self.title) or name, 'type': a.get('type', 'text'), 'options': []})
            if tag == 'select': field['type'] = 'select'; self.current = field
            elif a.get('type') == 'radio':
                field['type'] = 'select'
                value = a.get('value', '')
                if not any(o[0] == value for o in field['options']): field['options'].append([value, 'Увімкнено' if value == '1' else 'Вимкнено' if value == '0' else value])
            elif tag == 'textarea': field['type'] = 'textarea'
            if 'maxlength' in a: field['maxLength'] = int(a['maxlength'])
        if tag == 'option' and self.current is not None:
            self.option = [a.get('value', ''), '']; self.current['options'].append(self.option)
    def handle_endtag(self, tag):
        if tag in ('script', 'style'): self.in_script = False
        if tag == 'th': self.heading = False
        if tag == 'select': self.current = None
        if tag == 'option': self.option = None
    def handle_data(self, data):
        if self.in_script: return
        if self.heading: self.title += data
        if self.option is not None: self.option[1] += data

pages = {}
for band, suffix in [('24', '2g'), ('5', '')]:
    pages[band] = {}
    for section, classic in [('general', 'Wireless'), ('guest', 'WGuest'), ('bridge', 'WMode'), ('mac', 'ACL'), ('radius', 'WSecurity'), ('advanced', 'WAdvanced')]:
        filename = f'Advanced_{classic}{suffix}_Content.asp'
        raw = (SOURCE / filename).read_bytes()
        parser = Controls(); parser.feed(re.sub(r'<%.*?%>', '', raw.decode('utf-8'), flags=re.S))
        fields = list(parser.fields.values())
        for field in fields:
            if '_maclist_' in field['key']: field['label'] = 'MAC-адреса'
            if '_macdesc_' in field['key']: field['label'] = 'Опис пристрою'
            if field['label'] == 'b/g protection': field['label'] = 'Захист сумісності b/g'
            for option in field['options']: option[1] = label(option[1]) or option[0]
            # The inherited source also serves newer boards. WR1200JS is not AX.
            field['options'] = [o for o in field['options'] if 'ax' not in o[1].lower()]
            if field['key'].endswith(('_stream_tx', '_stream_rx')):
                # Exact board.h: BOARD_NUM_ANT_{2G,5G}_{TX,RX}=2.
                field['options'] = [o for o in field['options'] if o[0] in ('1', '2')]
            days = {'Mon':'Пн','Tue':'Вт','Wed':'Ср','Thu':'Чт','Fri':'Пт','Sat':'Сб','Sun':'Нд'}
            tail = field['key'].rsplit('_',1)[-1]
            if tail in days: field['label'] += ' · ' + days[tail]
            times = {'starthour':'початок, години','startmin':'початок, хвилини','endhour':'кінець, години','endmin':'кінець, хвилини'}
            if tail in times: field['label'] += ' · ' + times[tail]
        pages[band][section] = {'classic': filename, 'sha256': hashlib.sha256(raw).hexdigest(), 'fields': fields}
OUT.write_text(json.dumps({'demo': True, 'source': 'saved build 410 (inventory, not runtime acceptance)', 'pages': pages}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(f'Wrote {sum(len(p["fields"]) for b in pages.values() for p in b.values())} Classic controls; no NVRAM values copied')
