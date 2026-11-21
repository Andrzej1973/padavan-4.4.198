#!/usr/bin/env python3
"""Stage Modern IoT against the existing edit/view/result candidate only."""
import argparse
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent

def asset():
    controller=(HERE.parent/'iot/classic-config.js').read_text()
    if controller.count('}(window));')!=1:raise ValueError('IoT controller scope changed')
    controller=controller.replace('}(window));','}(context));',1)
    form=(HERE.parent/'iot/classic-config-form.html').read_text()
    return '''(function () {
 'use strict';
 let section;
 function ajax(options) {
  const abort=new AbortController();
  let settled=false;
  function finish(ok,value){
   if(settled)return;
   settled=true;clearTimeout(timer);
   if(ok)options.success(value);
   else if(options.error)options.error();
  }
  const timer=setTimeout(()=>{finish(false);abort.abort();},options.timeout||4000);
  const method=options.type||'GET';
  const values=new URLSearchParams(options.data||{});
  const url=options.url+(method==='GET'&&values.size?'?'+values.toString():'');
  const request={method,credentials:'same-origin',cache:'no-store',signal:abort.signal};
  if(method==='POST'){
   request.headers={'Content-Type':'application/x-www-form-urlencoded'};
   request.body=values.toString();
  }
  fetch(url,request).then(response=>{
   if(!response.ok)throw Error('request_failed');
   return response.json();
  }).then(reply=>finish(true,reply),()=>finish(false));
 }
 window.wrModernIot={render(panel){
  if(!section){
   section=document.createElement('section');
   section.className='wifi-iot-settings';
   section.innerHTML='''+json.dumps(form,ensure_ascii=False)+''';
   const context={document:{getElementById:id=>section.querySelector('#'+id)},
    jQuery:{ajax},setTimeout:window.setTimeout.bind(window)};
'''+controller+'''
   context.wrIotConfig.init();
  }
  panel.append(section);
 }};
}());
'''

def prepare(root):
    root=Path(root);modern=root/'trunk/user/www/modern'
    report=root/'modern-iot-candidate.json'
    if report.exists() or (modern/'modern-iot.js').exists():raise ValueError('Modern IoT already staged')
    meta=json.loads((root/'iot-edit-view-source.json').read_text())
    keys=('edit_startup_attempt_prepared','view_startup_attempt_prepared','native_capabilities_verified','http_view_bound','http_edit_bound','http_runtime_toggle_bound')
    if meta.get('board')!='WR1200JS' or not all(meta.get(k) is True for k in keys):
        raise ValueError('complete IoT edit/view candidate required')
    web=root/'trunk/user/httpd/web_ex.c';text=web.read_text()
    routes=[('token','NULL','wr_iot_http_token_output'),('view','wr_iot_http_apply_input','wr_iot_http_view_output'),('result','NULL','wr_iot_http_result_output')]
    routes += [('edit_'+s,'wr_iot_http_apply_input','wr_iot_http_edit_'+s+'_output') for s in ('ram','auto','save','runtime')]
    for name,inp,out in routes:
        route='{ "wr_iot_'+name+'.cgi", "application/json", no_cache_IE, '+inp+', '+out+', 1 }'
        if text.count(route)!=1:raise ValueError('missing authenticated IoT route: '+name)
    anchor='{ "modern/wifi.js", "text/javascript", no_cache_IE, NULL, do_file, 1 },'
    script='<script src="/modern/wifi.js" defer></script>'
    wifi=(modern/'wifi.js').read_text();index=(modern/'index.html').read_text()
    branch="    if (current.view==='iot') {"
    if text.count(anchor)!=1 or index.count(script)!=1 or wifi.count(branch)!=1:
        raise ValueError('Modern asset/renderer anchors changed')
    pending={web:text.replace(anchor,anchor+'\n\t{ "modern/modern-iot.js", "text/javascript", no_cache_IE, NULL, do_file, 1 },',1),
      modern/'wifi.js':wifi.replace(branch,branch+"\n      if(!schema.demo && window.wrModernIot){window.wrModernIot.render(panel);return;}",1),
      modern/'index.html':index.replace(script,'<script src="/modern/modern-iot.js" defer></script>\n  '+script,1),
      modern/'modern-iot.js':asset()}
    for path,data in pending.items():path.write_text(data)
    report.write_text(json.dumps({'board':'WR1200JS','candidate_only':True,'uses_existing_iot_protocol':True,
      'target_verified':False,'runtime_verified':False,'sha256':{str(p.relative_to(root)):hashlib.sha256(d.encode()).hexdigest() for p,d in pending.items()}},indent=2)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('source',type=Path)
    prepare(parser.parse_args().source)
    print('PASS Modern IoT candidate staged against authenticated existing IoT routes; target/device acceptance pending')
