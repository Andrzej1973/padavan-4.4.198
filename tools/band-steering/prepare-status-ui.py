#!/usr/bin/env python3
"""Add explicit refresh UI; no automatic service activation or background polling."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('source',type=Path)
a=p.parse_args()
root=a.source/'trunk/user/www'
f=root/'n56u_ribbon_fixed/Advanced_WAdvanced2g_Content.asp'
s=f.read_text(encoding='utf-8')
anchor='<#WR_BS_Help#></p>'
script='<script type="text/javascript" src="/jquery.js"></script>'
if s.count(anchor)!=1 or s.count(script)!=1 or 'wr_bs_refresh' in s:
 raise ValueError('Status UI anchors changed; no files written')
labels={
 'EN.footer': ('Refresh status','Checking…','State unknown','Daemon reports ACTIVE','Last verified OFF'),
 'UK.dict': ('Оновити стан','Перевіряється…','Стан невідомий','Демон повідомляє ACTIVE','Останнє підтвердження OFF'),
 'RU.dict': ('Обновить состояние','Проверяется…','Состояние неизвестно','Демон сообщает ACTIVE','Последнее подтверждение OFF')}
changes=[]
keys=('Refresh','Wait','Unknown','Active','Off')
for name,values in labels.items():
 path=root/'dict'/name
 text=path.read_text(encoding='utf-8')
 if 'WR_BS_Status_' in text: raise ValueError('Status keys already present')
 changes.append((path,text.rstrip('\n')+'\n'+''.join('WR_BS_Status_'+k+'='+v+'\n' for k,v in zip(keys,values))))
extra='<button type="button" class="btn" id="wr_bs_refresh" onclick="wrBandRefresh()"><#WR_BS_Status_Refresh#></button> '
extra+='<span id="wr_bs_status"'
for name,key in zip(('wait','unknown','active','off'),keys[1:]):
 extra+=' data-'+name+'="<#WR_BS_Status_'+key+'#>"'
extra+='><#WR_BS_Status_Unknown#></span>'
s=s.replace(anchor,anchor+'\n'+extra)
s=s.replace(script,script+'\n<script type="text/javascript" src="/wr-band-status.js"></script>')
js=(Path(__file__).parent/'status-ui.js').read_text(encoding='utf-8')
asset=root/'n56u_ribbon_fixed/wr-band-status.js'
if asset.exists(): raise ValueError('Status asset already exists')
for path,text in [(f,s),(asset,js)]+changes:
 path.write_text(text,encoding='utf-8')
print('Added explicit status refresh with serial gate and bounded polling')
