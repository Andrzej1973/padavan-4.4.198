const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
let events={},formEvents={},rendered=[],fail=false;
const box={innerHTML:'',style:{display:'none'},removeAttribute(k){delete this[k];}};
const message={textContent:'',getAttribute(k){return k==='data-error'?'ERROR':'UNSAVED';}};
const fields={};for(const band of ['rt','wl']) for(const [k,v] of Object.entries({ssid:'Home',auth_mode:'psk',wep_x:'0',wpa_psk:'password',closed:'0'}))fields[band+'_'+k]={value:v};
const context={document:{form:{elements:fields,addEventListener(k,f){formEvents[k]=f;}},getElementById(k){return k==='wr_wifi_qr'?box:message;},addEventListener(k,f){events[k]=f;}},window:{addEventListener(k,f){events[k]=f;}},wrWifiQrPayload:require('./wifi-qr-payload.js'),WRWifiQRCode:function(el,o){if(fail)throw Error('render');rendered.push(o.text);el.innerHTML='canvas';el.title=o.text;}};
vm.createContext(context);vm.runInContext(fs.readFileSync(__dirname+'/wifi-qr-preview.js','utf8'),context);events.DOMContentLoaded();
for(const band of ['rt','wl']){context.wrWifiQrShow(band);assert.equal(box.style.display,'inline-block');assert.equal(message.textContent,'UNSAVED');assert.equal(box.title,undefined);for(const event of ['input','change']){formEvents[event]();assert.equal(box.innerHTML,'');assert.equal(message.textContent,'');context.wrWifiQrShow(band);}events.pagehide();assert.equal(box.innerHTML,'');}
fields.rt_auth_mode.value='radius';context.wrWifiQrShow('rt');assert.equal(message.textContent,'ERROR');assert.equal(box.innerHTML,'');
fields.rt_auth_mode.value='psk';fail=true;context.wrWifiQrShow('rt');assert.equal(message.textContent,'ERROR');assert.equal(box.style.display,'none');
fail=false;fields.wl_closed=[{value:'0',checked:false},{value:'1',checked:true}];context.wrWifiQrShow('wl');assert.match(rendered.at(-1),/H:true/);
context.wrWifiQrShow('invalid');assert.equal(box.innerHTML,'');
console.log('Wi-Fi QR preview DOM fixture passed: both radios, edit/change/pagehide clearing, errors, hidden radio fallback, no credential tooltip.');
