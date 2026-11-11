#!/usr/bin/env python3
"""Opt-in Windows Edge visual check on loopback fixtures; never contacts router."""
import http.server
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import threading

here=Path(__file__).resolve().parent
public=here/'public'
schema=json.loads((public/'wifi-schema.json').read_text());schema['demo']=False
data=json.loads((here/'data/dashboard.json').read_text());data['demo']=False
band=dict(ssid='YOUHUA-5G',auth_mode='psk',wep_x='0',wpa_mode='2',crypto='aes',radio_x='1',closed='0',channel='0',HT_BW='2',gmode='4',HT_EXTCHA='1',country_code='UA',radio_date_x='0111110',radio_time_x='08002200',radio_time2_x='10002300')
data['wifiConfiguration']=dict(schemaVersion=1,source='stored-nvram',runtimeVerified=False,shared='1',bands={'24':dict(band,ssid='Shared fixture'),'5':band})
requests=[]
class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_GET(self):
        route=self.path.split('?',1)[0];requests.append(('GET',route))
        if route in ('/wr_modern.json','/api/dashboard.json'):body=json.dumps(data).encode();mime='application/json'
        elif route=='/wifi-schema.json':body=json.dumps(schema).encode();mime='application/json'
        else:
            path=here.parent/'shared-wifi/ui.js' if route=='/shared-wifi.js' else public/('index.html' if route=='/' else route.lstrip('/'))
            if not path.is_file() or not (path.resolve().is_relative_to(public.resolve()) or route=='/shared-wifi.js'):
                self.send_error(404);return
            body=path.read_bytes();mime={'.html':'text/html','.css':'text/css','.js':'text/javascript','.svg':'image/svg+xml'}.get(path.suffix,'application/octet-stream')
        self.send_response(200);self.send_header('Content-Type',mime+'; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(body)
    def do_POST(self):
        requests.append(('POST',self.path));self.send_error(405)

ps=r'''
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=[Text.UTF8Encoding]::new($false)
$profilePath='PROFILE_PATH'
$argsList=@('--headless=new','--disable-gpu','--no-first-run','--no-default-browser-check','--disable-background-networking','--disable-extensions',('--user-data-dir='+$profilePath),'--remote-debugging-port=0','about:blank')
$edge=Start-Process -FilePath 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe' -ArgumentList $argsList -PassThru
$ws=$null
try {
 $portFile=Join-Path $profilePath 'DevToolsActivePort'
 for($i=0;$i -lt 100 -and !(Test-Path $portFile);$i++){Start-Sleep -Milliseconds 100}
 if(!(Test-Path $portFile)){throw 'Fresh Edge debug endpoint not available'}
 $port=(Get-Content $portFile)[0]
 $targets=Invoke-RestMethod ('http://127.0.0.1:'+$port+'/json/list')
 $target=$targets|Where-Object {$_.type -eq 'page'}|Select-Object -First 1
 $ws=New-Object System.Net.WebSockets.ClientWebSocket
 $null=$ws.ConnectAsync([Uri]$target.webSocketDebuggerUrl,[Threading.CancellationToken]::None).GetAwaiter().GetResult()
 $script:sequence=0
 function Call-Cdp($method,$parameters){
  $script:sequence++;$id=$script:sequence
  $message=@{id=$id;method=$method;params=$parameters}|ConvertTo-Json -Depth 40 -Compress
  $bytes=[Text.Encoding]::UTF8.GetBytes($message)
  $null=$ws.SendAsync([ArraySegment[byte]]::new($bytes),[Net.WebSockets.WebSocketMessageType]::Text,$true,[Threading.CancellationToken]::None).GetAwaiter().GetResult()
  while($true){
   $stream=New-Object IO.MemoryStream
   do {
    $buffer=New-Object byte[] 65536
    $received=$ws.ReceiveAsync([ArraySegment[byte]]::new($buffer),[Threading.CancellationToken]::None).GetAwaiter().GetResult()
    if($received.MessageType -eq [Net.WebSockets.WebSocketMessageType]::Close){throw 'Edge socket closed'}
    $stream.Write($buffer,0,$received.Count)
   }while(!$received.EndOfMessage)
   $reply=[Text.Encoding]::UTF8.GetString($stream.ToArray())|ConvertFrom-Json
   $stream.Dispose()
   if($reply.id -eq $id){if($reply.error){throw ($reply.error|ConvertTo-Json -Compress)};return $reply.result}
  }
 }
 $null=Call-Cdp 'Page.enable' @{}
 $reports=@()
 foreach($width in @(1536,390)){
  $null=Call-Cdp 'Emulation.setDeviceMetricsOverride' @{width=$width;height=1100;deviceScaleFactor=1;mobile=($width -eq 390)}
  $null=Call-Cdp 'Page.navigate' @{url='PAGE_URL'}
  $expression=@'
(async()=>{for(let i=0;i<100;i++){const p=document.getElementById('modern-wifi');if(p&&!p.hidden&&p.querySelector('.wifi-general-five')&&Array.from(p.querySelectorAll('input')).some(x=>x.value==='YOUHUA-5G'))break;await new Promise(r=>setTimeout(r,100));}const p=document.getElementById('modern-wifi');return {width:innerWidth,documentWidth:document.documentElement.scrollWidth,clientWidth:document.documentElement.clientWidth,headings:Array.from(p.querySelectorAll('h2')).map(x=>x.textContent),values:Array.from(p.querySelectorAll('input')).map(x=>x.value),disabled:Array.from(p.querySelectorAll('input')).every(x=>x.disabled),forms:p.querySelectorAll('form').length,buttons:p.querySelectorAll('button').length,visible:!p.hidden,shared:p.textContent.includes('Назва та захист спільні для 2,4 і 5 ГГц')}})()
'@
  $expression=$expression.Replace('const p=document.getElementById(''modern-wifi'');return {','const p=document.getElementById(''modern-wifi'');document.querySelector(''.preview-banner'').textContent=''LOCAL FIXTURE - no router connection'';return {')
  $result=Call-Cdp 'Runtime.evaluate' @{expression=$expression;awaitPromise=$true;returnByValue=$true}
  if($result.exceptionDetails){throw ($result.exceptionDetails|ConvertTo-Json -Depth 10)}
  $metrics=$result.result.value
  $shot=Call-Cdp 'Page.captureScreenshot' @{format='png';captureBeyondViewport=$true;fromSurface=$true}
  $path=Join-Path 'OUTPUT_PATH' ('page04-'+$width+'.png')
  [IO.File]::WriteAllBytes($path,[Convert]::FromBase64String($shot.data))
  $reports+=@{requestedWidth=$width;metrics=$metrics;screenshot=$path}
 }
 Write-Output ('PAGE04_RESULT '+($reports|ConvertTo-Json -Depth 20 -Compress))
 $null=Call-Cdp 'Browser.close' @{}
} finally {
 if($ws){$ws.Dispose()}
 if(!$edge.WaitForExit(5000)){Stop-Process -Id $edge.Id -Force -ErrorAction SilentlyContinue}
}
'''
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
phase=Path(tempfile.mkdtemp(prefix='wr-page04-browser-',dir='/mnt/c/Users/ANDRZEJ/AppData/Local/Temp'))
profile=phase/'profile';profile.mkdir()
win=lambda p:subprocess.check_output(['wslpath','-w',str(p)],text=True).strip()
script=ps.replace('PROFILE_PATH',win(profile)).replace('OUTPUT_PATH',win(phase)).replace('PAGE_URL',f'http://127.0.0.1:{server.server_port}/#wifi/split/5/general')
completed=False
try:
    result=subprocess.run(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe','-NoProfile','-Command',script],capture_output=True,text=True,timeout=55)
    if result.returncode:raise RuntimeError(result.stderr[-6000:]+result.stdout[-1000:])
    completed=True
    rows=[line[len('PAGE04_RESULT '):] for line in result.stdout.splitlines() if line.startswith('PAGE04_RESULT ')]
    if len(rows)!=1:raise RuntimeError('Missing unique browser report: '+repr(result.stdout[:1500]))
    report=json.loads(rows[0])
    (phase/'metrics.json').write_text(json.dumps(report,indent=2)+'\n')
    for row in report:
        m=row['metrics'];assert m['width']==row['requestedWidth']
        assert m['visible'] and m['disabled'] and not m['forms'] and not m['buttons'] and m['shared']
        assert 'Основна мережа 5 ГГц' in m['headings'] and 'Розклад роботи' in m['headings']
        assert 'UA' in m['values'] and '08:00 – 22:00' in m['values']
        row['horizontalOverflow']=m['documentWidth']>m['clientWidth']
        assert not row['horizontalOverflow'],row
    assert not any(method!='GET' for method,_ in requests)
    print(json.dumps({'phase':str(phase),'report':report,'scope':'Actual assets/Edge CDP, fixture values only; no router or production write'},ensure_ascii=False))
finally:
    server.shutdown();server.server_close();thread.join()
    if completed:
        size=sum(p.stat().st_size for p in profile.rglob('*') if p.is_file())
        shutil.rmtree(profile);assert not profile.exists()
        print('Removed owned browser profile bytes',size,'screenshots retained for visual inspection in',phase)
    else:
        print('Retained browser profile pending process-lifetime verification',phase)
