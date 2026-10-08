/* Local unsaved form preview. Never submits or persists Wi-Fi credentials. */
function wrWifiQrHide() {
 var box=document.getElementById('wr_wifi_qr');
 if (!box) return;
 box.innerHTML=''; box.removeAttribute('title'); box.style.display='none';
 var message=document.getElementById('wr_wifi_qr_message');
 if (message) message.textContent='';
}
function wrWifiQrShow(band) {
 wrWifiQrHide();
 var form=document.form;
 var box=document.getElementById('wr_wifi_qr');
 var message=document.getElementById('wr_wifi_qr_message');
 if (!form || !box || !message || (band!=='rt' && band!=='wl')) return;
 function value(suffix) {
  var field=form.elements[band+'_'+suffix];
  if (!field) return '';
  if (typeof field.value==='string') return field.value;
  for(var i=0;i<field.length;i++) if(field[i].checked) return field[i].value;
  return '';
 }
 var result=wrWifiQrPayload({ssid:value('ssid'),auth:value('auth_mode'),
  wep:value('wep_x'),password:value('wpa_psk'),hidden:value('closed')});
 if (result.error) {message.textContent=message.getAttribute('data-error');return;}
 try {
  box.style.display='inline-block';
  new WRWifiQRCode(box,{text:result.payload,width:240,height:240});
  box.removeAttribute('title');
  message.textContent=message.getAttribute('data-preview');
 } catch(error) {
  wrWifiQrHide(); message.textContent=message.getAttribute('data-error');
 }
}
document.addEventListener('DOMContentLoaded',function(){
 if (!document.form) return;
 document.form.addEventListener('input',wrWifiQrHide);
 document.form.addEventListener('change',wrWifiQrHide);
});
window.addEventListener('pagehide',wrWifiQrHide);
