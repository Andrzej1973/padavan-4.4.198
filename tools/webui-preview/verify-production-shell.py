#!/usr/bin/env python3
"""HTTP checks for the loopback production-shell fixture; server must be running."""
import json
import os
import urllib.error
import urllib.request
from html.parser import HTMLParser

BASE=f"http://127.0.0.1:{os.environ.get('PADAVAN_PREVIEW_PORT','8080')}"

def get(path,method='GET',data=None):
 try:
  request=urllib.request.Request(BASE+path,method=method,data=data)
  with urllib.request.urlopen(request,timeout=3) as response:
   return response.status,response.read()
 except urllib.error.HTTPError as exc:
  return exc.code,exc.read()

class Resources(HTMLParser):
 def __init__(self):super().__init__();self.paths=[];self.forms=0
 def handle_starttag(self,tag,attrs):
  values=dict(attrs)
  if tag=='form':self.forms+=1
  for key in ('href','src'):
   value=values.get(key,'')
   if value.startswith('/modern/'):self.paths.append(value.split('#',1)[0])

status,health=get('/__health')
assert status==200
assert json.loads(health)['mode']=='read-only-production-shell'
status,html=get('/modern/index.html')
assert status==200
text=html.decode('utf-8')
assert '<title>Padavan Modern — WR1200JS</title>' in text
assert 'PADAVAN MODERN · LIVE READ-ONLY' in text
assert 'ЛОКАЛЬНЕ DEMO' not in text
parser=Resources();parser.feed(text)
assert parser.forms==0
for path in parser.paths:
 status,_=get(path)
 assert status==200,path
status,payload=get('/wr_modern.json')
assert status==200
data=json.loads(payload)
assert data['demo'] is False
assert len(data['pages'])==11
assert len(data['serviceTiles'])==14
assert data['iot']['status']=='Не підтверджено'
for method in ('POST','PUT','PATCH','DELETE','OPTIONS'):
 status,_=get('/',method,b'x' if method in ('POST','PUT','PATCH') else None)
 assert status==405,method
print('PASS production shell HTTP, assets, live JSON schema and read-only methods')
