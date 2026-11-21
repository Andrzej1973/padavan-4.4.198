#!/usr/bin/env python3
"""Opt-in real Windows Edge DOM check; mocked AJAX, no router or HTTP server."""
import ast
import base64
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

here=Path(__file__).resolve().parent
# Reuse the existing, reviewed Edge/CDP lifecycle without executing its Modern
# fixture or changing Modern sources. Refuse controller drift before launch.
tree=ast.parse((here.parent/'webui-preview/check_page04_browser.py').read_text())
ps=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
        and any(isinstance(t,ast.Name) and t.id=='ps' for t in n.targets))
assert ps.count(' $reports=@()')==1 and ps.count(" $null=Call-Cdp 'Browser.close'")==1
prefix=ps[:ps.index(' $reports=@()')]
suffix=ps[ps.index(" $null=Call-Cdp 'Browser.close'"):]
html='''<!doctype html><meta charset="utf-8"><title>Classic IoT browser fixture</title>
<div id="TopBanner"><a id="wifi5_b">5GHz</a><a id="wifi5_b_g">Guest5</a></div>
<div id="subMenu"></div><div><div id="tabMenu"></div></div>
'''+(here/'classic-config-form.html').read_text()+'''
<script>window.testErrors=[];window.addEventListener('error',e=>testErrors.push(e.message));
window.calls=[];window.jQuery={ajax:c=>calls.push(c)};</script>
<script>'''+(here/'classic-config.js').read_text()+'''</script><script>
wrIotConfig.init();</script><script>'''+(here/'classic-navigation.js').read_text()+'''</script>'''
expression=r'''
(async()=>{
 const assert=(v,m)=>{if(!v)throw new Error(m)},id=n=>document.getElementById('iot-'+n);
 for(let i=0;i<50&&!document.getElementById('wr-classic-iot-menu');i++)await new Promise(r=>setTimeout(r,50));
 assert(document.getElementById('wr-classic-iot-menu'),'navigation mounted');
 assert(document.getElementById('wifi_iot_b')&&document.getElementById('wifi_iot_b_g'),'Main/Guest IoT shortcuts');
 assert(document.getElementById('wifi5_b')&&document.getElementById('wifi5_b_g'),'original shortcuts retained');
 assert(id('save').disabled&&!id('refresh').disabled&&calls.length===0,'no automatic read/write');
 function load(configured=true){
  id('refresh').click();let c=calls.shift();assert(c.url==='/wr_iot_token.cgi','token read');c.success({token:'a'.repeat(32)});
  c=calls.shift();assert(c.url==='/wr_iot_view.cgi'&&c.type==='POST','guarded view POST');
  c.success({revision:'b'.repeat(32),configured,enabled:false,key_present:configured,ssid:configured?'<img src=x>':'',gateway:configured?'192.168.50.1':'',mask:configured?'255.255.255.0':'',first:configured?'192.168.50.20':'',last:configured?'192.168.50.200':''});
 }
 const results=[];
 for(const mode of ['ram','auto','save']){
  load();assert(id('ssid').value==='<img src=x>'&&!document.querySelector('img'),'SSID remains text');
  assert(id('password').disabled,'KEEP hides key');
  id(mode).click();const c=calls.shift();assert(c.url==='/wr_iot_edit_'+mode+'.cgi'&&c.type==='POST','endpoint mode');
  assert(c.data.wr_iot_request_psk===''&&c.data.revision==='b'.repeat(32)&&c.data.key_action==='keep','KEEP request');
  id(mode).click();assert(calls.length===0,'disabled button cannot resubmit');
  c.success({accepted:true,id:'c'.repeat(32)});const poll=calls.shift();assert(poll.url==='/wr_iot_result.cgi','queued status only');
  poll.success({id:'c'.repeat(32),state:mode==='save'?'saved_in_flash':'stored_in_ram'});
  assert(id('password').value===''&&id(mode).disabled&&!id('refresh').disabled,'terminal needs fresh view');results.push(mode);
 }
 load(false);assert(id('action').value==='replace'&&!id('password').disabled,'first configuration requires key');
 id('password').value='fixture-password';id('ram').click();const replace=calls.shift();
 assert(replace.data.wr_iot_request_psk==='fixture-password','replacement intent');replace.error();
 assert(replace.data.wr_iot_request_psk===''&&id('password').value===''&&!calls.length,'uncertain submission wipes key and never retries');
 load();id('save').click();calls.shift().success({accepted:true,id:'d'.repeat(32)});
 calls.shift().success({id:'d'.repeat(32),state:'recovery_required'});
 assert(!calls.length&&id('message').textContent.includes('не повторюється'),'unknown result never replays');
 for(const [button,enabled] of [['on','1'],['off','0']]){
  load();id('ssid').value='Unsaved draft';id('action').value='replace';id('password').value='draft-password';
  id(button).click();const c=calls.shift();
  assert(c.url==='/wr_iot_edit_runtime.cgi'&&c.data.wr_iot_request_enable===enabled,'runtime endpoint');
  assert(c.data.wr_iot_request_ssid==='<img src=x>'&&c.data.key_action==='keep'&&c.data.wr_iot_request_psk==='','runtime uses captured view, not unsaved draft/key');
  c.success({accepted:true,id:'e'.repeat(32)});calls.shift().success({id:'e'.repeat(32),state:'applied'});
  assert(id(button).disabled&&id('message').textContent.includes('виконано'),'runtime terminal distinct from persistence');
 }
 const clock=Date.now;load();Date.now=()=>clock()+110001;id('save').click();Date.now=clock;
 assert(!calls.length&&id('save').disabled,'expired lease needs fresh read');
 load();Date.now=()=>0;id('ram').click();Date.now=clock;
 assert(!calls.length&&id('ram').disabled,'clock regression never submits');
 assert(!testErrors.length,'no page errors');
 return {browser:navigator.userAgent,modes:results,runtimeModes:['on','off'],navigation:true,secretWiped:true,automaticRetry:false,expiryRefused:true,clockRegressionRefused:true,pageErrors:testErrors,
         scope:'Real Edge DOM with actual form/config/navigation assets; AJAX and SDK frame are fixtures, no native HTTP/RC or device acceptance'};
})()
'''
middle=r'''
 $null=Call-Cdp 'Network.enable' @{}
 $null=Call-Cdp 'Network.setBlockedURLs' @{urls=@('*')}
 $tree=Call-Cdp 'Page.getFrameTree' @{}
 $html=[Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('HTML_BASE64'))
 $null=Call-Cdp 'Page.setDocumentContent' @{frameId=$tree.frameTree.frame.id;html=$html}
 $expression=@'
EXPRESSION
'@
 $result=Call-Cdp 'Runtime.evaluate' @{expression=$expression;returnByValue=$true;awaitPromise=$true}
 if($result.exceptionDetails){throw ($result.exceptionDetails|ConvertTo-Json -Depth 10)}
 Write-Output ('IOT_BROWSER_RESULT '+($result.result.value|ConvertTo-Json -Depth 20 -Compress))
'''
phase=Path(tempfile.mkdtemp(prefix='wr-iot-browser-',dir='/mnt/c/Users/ANDRZEJ/AppData/Local/Temp'))
profile=phase/'profile';profile.mkdir()
win=lambda p:subprocess.check_output(['wslpath','-w',str(p)],text=True).strip()
script=(prefix+middle+suffix).replace('PROFILE_PATH',win(profile)).replace('HTML_BASE64',base64.b64encode(html.encode()).decode()).replace('EXPRESSION',expression)
path=phase/'check.ps1';path.write_text(script,encoding='utf-8-sig')
completed=False
try:
 result=subprocess.run(['/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe','-NoProfile','-File',win(path)],capture_output=True,text=True,timeout=60)
 if result.returncode:raise RuntimeError(result.stderr[-5000:]+result.stdout[-1000:])
 rows=[line[len('IOT_BROWSER_RESULT '):] for line in result.stdout.splitlines() if line.startswith('IOT_BROWSER_RESULT ')]
 if len(rows)!=1:raise RuntimeError('Missing unique browser result: '+result.stdout[-1500:])
 report=json.loads(rows[0]);assert report['modes']==['ram','auto','save'] and not report['pageErrors']
 completed=True;print(json.dumps(report,ensure_ascii=False))
finally:
 if completed:
  shutil.rmtree(phase);assert not phase.exists()
  print('Removed owned browser profile and temporary script')
 else:print('Browser attempt failed; retain profile until process lifetime is checked:',phase)
