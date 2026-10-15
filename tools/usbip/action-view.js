var wrUSBIPActionRows=[],wrUSBIPActionTime=0,wrUSBIPActionBusy=false;
var wrUSBIPActionDaemon=2,wrUSBIPActionID='',wrUSBIPActionDeadline=0,wrUSBIPActionPolling=false;
function wrUSBIPActionUpdate() {
 var select=document.getElementById('wr_usbip_device_select');
 if(!select)return;
 var row=wrUSBIPActionRows[Number(select.value)];
 var valid=!wrUSBIPActionBusy && /^[0-9a-f]{32}$/.test(wrUSBIPActionToken) &&
  document.getElementById('wr_usbip_ack').checked && row &&
  /^[0-9a-fA-F]{4}$/.test(row.vendor) && /^[0-9a-fA-F]{4}$/.test(row.product) &&
  wrUSBIPActionTime>0 && Date.now()-wrUSBIPActionTime>=0 && Date.now()-wrUSBIPActionTime<=30000;
 document.getElementById('wr_usbip_bind').disabled=!(valid && row.exported===0 && wrUSBIPActionDaemon===1);
 document.getElementById('wr_usbip_unbind').disabled=!(valid && row.exported===1);
 select.disabled=wrUSBIPActionBusy;
}
function wrUSBIPActionDevices(rows) {
 var select=document.getElementById('wr_usbip_device_select');
 if(!select)return;
 wrUSBIPActionRows=rows||[];wrUSBIPActionTime=rows?Date.now():0;
 select.options.length=0;
 wrUSBIPActionRows.forEach(function(row,index){
  var option=document.createElement('option');option.value=String(index);
  option.textContent=row.busid+' '+(row.vendor||'?')+':'+(row.product||'?');select.appendChild(option);
 });
 wrUSBIPActionUpdate();
}
function wrUSBIPActionFinish(label) {
 wrUSBIPActionBusy=false;
 $j('#wr_usbip_action_result').text(label);wrUSBIPActionUpdate();
}
function wrUSBIPActionPoll() {
 if(!wrUSBIPActionID || wrUSBIPActionPolling)return;
 if(document.hidden){
  if(wrUSBIPActionBusy)window.setTimeout(wrUSBIPActionPoll,2000);
  return;
 }
 if(wrUSBIPActionBusy && Date.now()>wrUSBIPActionDeadline){wrUSBIPActionFinish(wrUSBIPActionLabels.unknown);return;}
 wrUSBIPActionPolling=true;
 $j.ajax({url:'/update.cgi',data:{output:'wr_usbip_job_state',arg0:wrUSBIPActionID},dataType:'json',cache:false,timeout:5000})
 .done(function(reply){
  if(!reply || reply.id!==wrUSBIPActionID || [1,2,3].indexOf(reply.state)<0 ||
     typeof reply.code!=='number' || Math.floor(reply.code)!==reply.code || reply.code< -1 || reply.code>255 ||
     (reply.state===1 && reply.code!==-1) || (reply.state===2 && reply.code!==0) || (reply.state===3 && reply.code===0)){
   wrUSBIPActionFinish(wrUSBIPActionLabels.unknown);return;
  }
  if(reply.state===1){
   if(!wrUSBIPActionBusy){wrUSBIPActionBusy=true;wrUSBIPActionDeadline=Date.now()+60000;wrUSBIPActionUpdate();}
   $j('#wr_usbip_action_result').text(wrUSBIPActionLabels.pending);
   if(wrUSBIPActionBusy)window.setTimeout(wrUSBIPActionPoll,2000);
  } else {
   wrUSBIPActionFinish(reply.state===2?wrUSBIPActionLabels.done:wrUSBIPActionLabels.failed);
   wrUSBIPInventoryRefresh();wrUSBIPRefresh();
  }
 })
 .fail(function(){wrUSBIPActionFinish(wrUSBIPActionLabels.unknown);})
 .always(function(){wrUSBIPActionPolling=false;});
}
function wrUSBIPActionSubmit(operation) {
 wrUSBIPActionUpdate();
 if(['bind','unbind'].indexOf(operation)<0 || document.getElementById('wr_usbip_'+operation).disabled)return;
 var row=wrUSBIPActionRows[Number(document.getElementById('wr_usbip_device_select').value)];
 wrUSBIPActionBusy=true;wrUSBIPActionID='';wrUSBIPActionUpdate();
 document.getElementById('wr_usbip_ack').checked=false;
 $j('#wr_usbip_action_result').text(wrUSBIPActionLabels.pending);
 $j.ajax({url:'/wr_usbip_action.cgi',type:'POST',dataType:'json',timeout:5000,
  data:{operation:operation,busid:row.busid,vendor:row.vendor,product:row.product,ack:'1',token:wrUSBIPActionToken}})
 .done(function(reply){
  if(!reply || reply.accepted!==true || typeof reply.id!=='string' || !/^[0-9a-f]{32}$/.test(reply.id)){
   wrUSBIPActionFinish(wrUSBIPActionLabels.unknown);return;
  }
  wrUSBIPActionID=reply.id;wrUSBIPActionDeadline=Date.now()+60000;wrUSBIPActionPoll();
 })
 .fail(function(){wrUSBIPActionFinish(wrUSBIPActionLabels.unknown);});
}
