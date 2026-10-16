var wrUSBIPSettingsRows=[],wrUSBIPSettingsLoaded=false,wrUSBIPSettingsBusy=false,wrUSBIPSettingsDirty=false;
function wrUSBIPSettingsValid(rows) {
 if(!Array.isArray(rows)||rows.length!==16)return false;
 var ports={},identities={};
 for(var i=0;i<16;i++)if(rows[i]!==null){
  var r=rows[i];if(!r||typeof r!=='object')return false;
  var identity=r.vendor+':'+r.product+':'+r.serial_hex;
  if(typeof r.busid!=='string'||r.busid.length>31||!/^\d+-\d+(\.\d+)*$/.test(r.busid)||
     !/^[0-9a-f]{4}$/.test(r.vendor)||!/^[0-9a-f]{4}$/.test(r.product)||
     typeof r.serial_hex!=='string'||r.serial_hex.length>512||!/^([0-9a-f]{2})+$/.test(r.serial_hex))return false;
  for(var j=0;j<r.serial_hex.length;j+=2){var n=parseInt(r.serial_hex.slice(j,j+2),16);if(n<32||n===127)return false;}
  if(ports[r.busid]||identities[identity])return false;
  ports[r.busid]=true;identities[identity]=true;
 }
 return true;
}
function wrUSBIPSettingsEncode(rows) {
 if(!wrUSBIPSettingsValid(rows))return null;
 var text='wr-usbip-exports-v1\n';
 rows.forEach(function(r){text+=r?'1\t'+r.busid+'\t'+r.vendor+'\t'+r.product+'\t'+r.serial_hex+'\n':'0\n';});
 var hex='';for(var i=0;i<text.length;i++)hex+=('0'+text.charCodeAt(i).toString(16)).slice(-2);
 return hex;
}
function wrUSBIPSettingsDecode(hex) {
 if(typeof hex!=='string'||hex.length>=18432||!/^([0-9a-f]{2})+$/.test(hex))return null;
 var text='';for(var i=0;i<hex.length;i+=2)text+=String.fromCharCode(parseInt(hex.slice(i,i+2),16));
 var lines=text.split('\n');if(lines.length!==18||lines.shift()!=='wr-usbip-exports-v1'||lines.pop()!=='')return null;
 var rows=lines.map(function(line){if(line==='0')return null;var f=line.split('\t');
  return f.length===5&&f[0]==='1'?{busid:f[1],vendor:f[2],product:f[3],serial_hex:f[4]}:false;});
 if(rows.indexOf(false)>=0||!wrUSBIPSettingsValid(rows))return null;return rows;
}
function wrUSBIPSettingsMessage(text){document.getElementById('wr_usbip_settings_result').textContent=text;}
function wrUSBIPSettingsRender() {
 var body=document.getElementById('wr_usbip_settings_rows');while(body.firstChild)body.removeChild(body.firstChild);
 wrUSBIPSettingsRows.forEach(function(r,index){if(!r)return;
  var tr=document.createElement('tr'),label=document.createElement('td'),action=document.createElement('td'),button=document.createElement('button');
  label.textContent=r.busid+' '+r.vendor+':'+r.product;button.type='button';button.className='btn';
  button.textContent=wrUSBIPSettingsLabels.remove;button.disabled=wrUSBIPSettingsBusy||!wrUSBIPSettingsLoaded;
  button.onclick=function(){wrUSBIPSettingsRows[index]=null;wrUSBIPSettingsDirty=true;wrUSBIPSettingsRender();};
  tr.appendChild(label);action.appendChild(button);tr.appendChild(action);body.appendChild(tr);
 });
 document.getElementById('wr_usbip_settings_save').disabled=wrUSBIPSettingsBusy||!wrUSBIPSettingsLoaded;
 document.getElementById('wr_usbip_settings_add').disabled=wrUSBIPSettingsBusy||!wrUSBIPSettingsLoaded;
}
function wrUSBIPSettingsLoad() {
 if(wrUSBIPSettingsBusy)return;
 if(wrUSBIPSettingsDirty&&!window.confirm(wrUSBIPSettingsLabels.discard))return;
 wrUSBIPSettingsBusy=true;wrUSBIPSettingsLoaded=false;wrUSBIPSettingsRender();
 wrUSBIPSettingsMessage(wrUSBIPSettingsLabels.loading);
 $j.ajax({url:'/update.cgi',data:{output:'wr_usbip_export_settings'},dataType:'json',cache:false,timeout:5000})
 .done(function(reply){
  var rows=reply&&(reply.state===1||reply.state===2)?wrUSBIPSettingsDecode(reply.table_hex):null;
  if(!rows){wrUSBIPSettingsMessage(wrUSBIPSettingsLabels.unknown);return;}
  wrUSBIPSettingsRows=rows;wrUSBIPSettingsLoaded=true;wrUSBIPSettingsDirty=false;
  document.getElementById('wr_usbip_settings_ack').checked=false;wrUSBIPSettingsMessage(wrUSBIPSettingsLabels.loaded);
 }).fail(function(){wrUSBIPSettingsMessage(wrUSBIPSettingsLabels.unknown);})
 .always(function(){wrUSBIPSettingsBusy=false;wrUSBIPSettingsRender();});
}
function wrUSBIPSettingsAdd() {
 if(wrUSBIPSettingsBusy||!wrUSBIPSettingsLoaded)return;
 var selected=document.getElementById('wr_usbip_device_select'),r=wrUSBIPActionRows[Number(selected.value)];
 var rows=wrUSBIPSettingsRows.slice(),slot=rows.indexOf(null),age=Date.now()-wrUSBIPActionTime;
 if(!r||slot<0||!wrUSBIPActionTime||age<0||age>30000){wrUSBIPSettingsMessage(wrUSBIPSettingsLabels.invalid);return;}
 rows[slot]={busid:r.busid,vendor:r.vendor.toLowerCase(),product:r.product.toLowerCase(),serial_hex:r.serial_hex};
 if(!wrUSBIPSettingsValid(rows)){wrUSBIPSettingsMessage(wrUSBIPSettingsLabels.invalid);return;}
 wrUSBIPSettingsRows=rows;wrUSBIPSettingsDirty=true;wrUSBIPSettingsRender();wrUSBIPSettingsMessage(wrUSBIPSettingsLabels.draft);
}
function wrUSBIPSettingsSave() {
 if(wrUSBIPSettingsBusy||!wrUSBIPSettingsLoaded)return;
 var table=wrUSBIPSettingsEncode(wrUSBIPSettingsRows);
 if(!table||!/^[0-9a-f]{32}$/.test(wrUSBIPActionToken)||!document.getElementById('wr_usbip_settings_ack').checked){
  wrUSBIPSettingsMessage(wrUSBIPSettingsLabels.confirm);return;
 }
 wrUSBIPSettingsBusy=true;document.getElementById('wr_usbip_settings_ack').checked=false;wrUSBIPSettingsRender();
 wrUSBIPSettingsMessage(wrUSBIPSettingsLabels.loading);
 $j.ajax({url:'/wr_usbip_settings.cgi',type:'POST',dataType:'json',timeout:5000,
  data:{token:wrUSBIPActionToken,ack:'1',table_hex:table}})
 .done(function(reply){
  if(!reply||reply.saved!==true||typeof reply.synchronized!=='boolean'||reply.applied!==false||reply.flash_committed!==false){
   wrUSBIPSettingsLoaded=false;wrUSBIPSettingsMessage(wrUSBIPSettingsLabels.unknown);return;
  }
  wrUSBIPSettingsDirty=false;wrUSBIPSettingsMessage(reply.synchronized?wrUSBIPSettingsLabels.saved:wrUSBIPSettingsLabels.unsynced);
 }).fail(function(){wrUSBIPSettingsLoaded=false;wrUSBIPSettingsMessage(wrUSBIPSettingsLabels.unknown);})
 .always(function(){wrUSBIPSettingsBusy=false;wrUSBIPSettingsRender();});
}
