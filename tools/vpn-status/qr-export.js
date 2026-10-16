/* Local VPN QR uses the same UTF-8 renderer as Wi-Fi. Never sends keys to a QR service. */
var wrVPNQR={generation:0,index:-1,payload:null,filename:'',xhr:null,baseline:null};
function wrVPNQrFingerprint(){
 var fields=document.form.elements,values=[];
 for(var i=0;i<fields.length;i++){
  var f=fields[i];if(!f.name || f.name.indexOf('vpns_')!==0)continue;
  values.push([f.name,String(f.value),!!f.checked]);
 }
 return JSON.stringify(values);
}
function wrVPNQrCapture(){wrVPNQR.baseline=wrVPNQrFingerprint();}
function wrVPNQrReset(){
 wrVPNQR.generation++;
 var old=wrVPNQR.xhr;wrVPNQR.xhr=null;
 wrVPNQR.index=-1;wrVPNQR.payload=null;wrVPNQR.filename='';
 if(old)old.abort();
 for(var i=0;i<ACLList.length;i++){
  var ids=['wg_client','wg_client_config','wg_client_file'];
  for(var j=0;j<ids.length;j++){
   var el=document.getElementById(ids[j]+i);
   if(el){el.textContent='';if(ids[j]==='wg_client')el.innerHTML='';el.removeAttribute('title');}
  }
  var toggle=document.getElementById('showqr'+i);if(toggle)toggle.textContent=' +';
  showhide_div('ACLList_Block_qr'+i,0);
  showhide_div('wg_row_conf'+i,0);
 }
}
function wrVPNQrMessage(value){var el=document.getElementById('wr_vpn_qr_message');if(el)el.textContent=value;}
function wrVPNQrPayload(value){
 if(typeof value!=='string'||!value.length||value.length>4096)return null;
 var text=value.replace(/\r\n/g,'\n');
 if(text.indexOf('\x00')!==-1||text.indexOf('\r')!==-1)return null;
 if((text.match(/^\[Interface\]\s*$/gm)||[]).length!==1 || (text.match(/^\[Peer\]\s*$/gm)||[]).length!==1)return null;
 if(!/^PrivateKey\s*=\s*[A-Za-z0-9+/]{43}=\s*$/m.test(text)||!/^PublicKey\s*=\s*[A-Za-z0-9+/]{43}=\s*$/m.test(text))return null;
 return text;
}
function export_client_wg(num){
 if(!login_safe()||wrVPNQR.index!==Number(num)||!wrVPNQR.payload || wrVPNQR.baseline!==wrVPNQrFingerprint())return false;
 var blob=new Blob([wrVPNQR.payload],{type:'text/plain;charset=utf-8'}),url=URL.createObjectURL(blob);
 var a=document.createElement('a');a.href=url;a.download=wrVPNQR.filename;
 document.body.appendChild(a);a.click();document.body.removeChild(a);window.setTimeout(function(){URL.revokeObjectURL(url);},1000);
 return false;
}
function export_client_wg_qr(num){
 var index=Number(num);
 if(!login_safe()||!isFinite(index)||Math.floor(index)!==index||index<0||index>=ACLList.length||!ACLList[index][0])return false;
 var closing=wrVPNQR.index===index;wrVPNQrReset();wrVPNQrMessage('');
 if(closing)return false;
 if(wrVPNQR.baseline===null||wrVPNQR.baseline!==wrVPNQrFingerprint()){
  wrVPNQrMessage(wrVPNQrLabels.changed);return false;
 }
 wrVPNQR.index=index;
 var generation=wrVPNQR.generation,name=String(ACLList[index][0]);
 wrVPNQrMessage(wrVPNQrLabels.loading);
 wrVPNQR.xhr=$j.ajax({url:'/apply.cgi',type:'POST',dataType:'text',timeout:10000,
  data:{action_mode:' ExportWGConf ',common_name:name}})
 .done(function(response){
  if(generation!==wrVPNQR.generation)return;
  if(!ACLList[index]||String(ACLList[index][0])!==name||wrVPNQR.baseline!==wrVPNQrFingerprint()){wrVPNQrReset();wrVPNQrMessage(wrVPNQrLabels.changed);return;}
  var payload=wrVPNQrPayload(response),box=document.getElementById('wg_client'+index);
  if(!payload||!box){wrVPNQrReset();wrVPNQrMessage(wrVPNQrLabels.error);return;}
  try{
   box.style.backgroundColor='white';box.style.padding='16px';
   new WRWifiQRCode(box,{text:payload,width:256,height:256});box.removeAttribute('title');
   wrVPNQR.payload=payload;
   wrVPNQR.filename=name.replace(/[^A-Za-z0-9_.-]/g,'_').slice(0,64)+'_vpn.conf';
   document.getElementById('wg_client_config'+index).textContent=payload;
   document.getElementById('wg_client_file'+index).textContent=wrVPNQR.filename;
   document.getElementById('showqr'+index).textContent=' −';
   showhide_div('ACLList_Block_qr'+index,1);showhide_div('wg_row_conf'+index,1);
   wrVPNQrMessage(wrVPNQrLabels.private);
  }catch(error){wrVPNQrReset();wrVPNQrMessage(wrVPNQrLabels.error);}
 })
 .fail(function(){if(generation===wrVPNQR.generation){wrVPNQrReset();wrVPNQrMessage(wrVPNQrLabels.error);}})
 .always(function(){if(generation===wrVPNQR.generation)wrVPNQR.xhr=null;});
 return false;
}
document.addEventListener('DOMContentLoaded',function(){
 function changed(){wrVPNQrReset();wrVPNQrMessage(wrVPNQrLabels.changed);}
 document.form.addEventListener('input',changed);document.form.addEventListener('change',changed);
});
window.addEventListener('pagehide',function(){wrVPNQrReset();wrVPNQR.baseline=null;});
