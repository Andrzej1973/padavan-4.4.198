'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const script=fs.readFileSync(process.argv[2],'utf8');
const tick=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
 for(const mode of ['ram','auto','save','runtime']){
  const nodes={};let section,requests=[],server={ssid:'IoT <stored>',gateway:'192.168.50.1',mask:'255.255.255.0',first:'192.168.50.20',last:'192.168.50.200'};
  const token='a'.repeat(32),revision='b'.repeat(32),id='c'.repeat(32);let transactionId=id;
  const panel={append(node){section=node;}};
  let fail=false;
  const window={setTimeout};
  vm.runInNewContext(script,{window,document:{createElement(){return {set innerHTML(html){
    for(const match of html.matchAll(/id="([^"]+)"/g))nodes[match[1]]={value:match[1]==='iot-action'?'keep':'',checked:false,disabled:false,textContent:''};
   },querySelector(sel){return nodes[sel.slice(1)];}};}},AbortController,URLSearchParams,setTimeout,clearTimeout,
   fetch:async(url,options)=>{
    requests.push({url,options});assert.equal(options.credentials,'same-origin');assert.equal(options.cache,'no-store');
    if(options.method==='POST'&&process.argv[3]&&process.argv[4]!=='--handlers'){
     const checked=require('node:child_process').spawnSync(process.argv[3],
       [url,options.headers['Content-Type'],options.body,token],{encoding:'utf8'});
     assert.equal(checked.status,0,'native HTTP input rejected '+url+': '+checked.stderr);
    }
    if(fail)throw Error('lost');
    let result;
    if(url==='/wr_iot_token.cgi')result={token};
    else if(url==='/wr_iot_view.cgi'){
     assert.equal(options.method,'POST');assert.equal(new URLSearchParams(options.body).get('token'),token);
     result={revision,configured:true,enabled:false,key_present:true,...server};
    }else if(url.startsWith('/wr_iot_edit_')){
     const body=new URLSearchParams(options.body);
     assert.equal(body.get('revision'),revision);assert.equal(body.get('key_action'),'keep');
     assert.equal(body.get('wr_iot_request_psk'),'');
     server.ssid=body.get('wr_iot_request_ssid');result={accepted:true,id};
    }else if(url==='/wr_iot_result.cgi?id='+transactionId)result={id:transactionId,state:mode==='runtime'?'applied':mode==='save'?'saved_in_flash':'stored_in_ram'};
    else throw Error('Unexpected route '+url);
    if(process.argv[4]==='--handlers'){
     const native=require('node:child_process').spawnSync(process.argv[3],
      [url,options.headers?.['Content-Type']||'',options.body||'',token,server.ssid,mode],{encoding:'utf8'});
     assert.equal(native.status,0,'native HTTP handler failed: '+native.stderr);
     result=JSON.parse(native.stdout);
     if(url.startsWith('/wr_iot_edit_')){
      assert.equal(result.accepted,true);
      assert.match(result.id,/^[0-9a-f]{32}$/);
      transactionId=result.id;
     }
    }
    return {ok:true,json:async()=>result};
   }});
  window.wrModernIot.render(panel);
  assert(nodes['iot-save'].disabled);assert.equal(requests.length,0);
  nodes['iot-refresh'].onclick();await tick();await tick();
  assert.equal(nodes['iot-ssid'].value,'IoT <stored>');assert.equal(nodes['iot-password'].value,'');
  nodes['iot-ssid'].value='IoT changed & <value>';
  nodes[mode==='runtime'?'iot-on':'iot-'+mode].onclick();
  const same=section;window.wrModernIot.render(panel);assert.equal(section,same);
  nodes[mode==='runtime'?'iot-on':'iot-'+mode].onclick();
  await tick();await tick();
  const writes=requests.filter(r=>r.url.startsWith('/wr_iot_edit_'));
  assert.equal(writes.length,1);assert.equal(writes[0].url,'/wr_iot_edit_'+mode+'.cgi');
  assert(nodes['iot-message'].textContent.startsWith(mode==='runtime'?'Запит перемикання виконано.':mode==='save'?'Збережено у flash.':'Збережено в RAM.'),nodes['iot-message'].textContent);
  assert.equal(server.ssid,mode==='runtime'?'IoT <stored>':'IoT changed & <value>');
  assert.equal(nodes['iot-password'].value,'');
  nodes['iot-refresh'].onclick();await tick();await tick();
  assert.equal(nodes['iot-ssid'].value,server.ssid);
  fail=true;nodes['iot-ram'].onclick();await tick();await tick();
  const after=requests.length;nodes['iot-ram'].onclick();await tick();
  assert.equal(requests.length,after);assert(nodes['iot-save'].disabled);
 }
 console.log('PASS Modern IoT generated controller: real route names, token/revision, RAM/auto/flash/runtime request, result polling, saved-value reread, route-switch retention, single send, network-loss refusal; native mailbox covered by sibling handler fixture');
})().catch(e=>{console.error(e);process.exitCode=1;});
