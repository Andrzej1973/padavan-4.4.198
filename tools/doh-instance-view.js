function wrDoHRender(value){
 var labels=['<#WRDNSOff#>','<#WRDNSPresent#>','<#WRDNSAbsent#>','<#WRDNSUnknown#>','<#WRDNSStillPresent#>'];
 var names=['state','requested','configuredMask','ownedMask','unknownMask','duplicateMask'],valid=!!value&&typeof value==='object',i;
 for(i=0;valid&&i<names.length;i++){
  var n=value[names[i]],max=i===0?4:i===1?1:15;
  valid=typeof n==='number'&&isFinite(n)&&Math.floor(n)===n&&n>=0&&n<=max;
 }
 if(valid)valid=!(value.ownedMask&value.unknownMask)&&((value.duplicateMask&value.unknownMask)===value.duplicateMask);
 if(!valid){$j('#wr_dns_process_status').text(labels[3]);$j('#wr_doh_instances').text(labels[3]);return;}
 function slots(mask){var result=[];for(var bit=0;bit<4;bit++)if(mask&(1<<bit))result.push(bit+1);return result.length?result.join(', '):'<#WRDNSNoSlots#>';}
 $j('#wr_dns_process_status').text(labels[value.state]);
 $j('#wr_doh_instances').text(
  '<#WRDNSConfiguredSlots#>: '+slots(value.configuredMask)+'; '+
  '<#WRDNSOwnedSlots#>: '+slots(value.ownedMask)+'; '+
  '<#WRDNSMissingSlots#>: '+slots(value.configuredMask&~(value.ownedMask|value.unknownMask))+'; '+
  '<#WRDNSUnknownSlots#>: '+slots(value.unknownMask)+'; '+
  '<#WRDNSUnexpectedSlots#>: '+slots(value.ownedMask&~value.configuredMask)+'; '+
  '<#WRDNSDuplicateSlots#>: '+slots(value.duplicateMask));
}
