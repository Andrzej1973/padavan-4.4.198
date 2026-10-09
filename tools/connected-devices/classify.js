/* Browser-only, bounded heuristics. No scans, network lookups or exact probabilities. */
(function(root,factory){
  if(typeof module==='object'&&module.exports)module.exports=factory();
  else root.WRDeviceClassification=factory();
})(typeof window!=='undefined'?window:this,function(){
  'use strict';
  var categories=['Android','Windows','Apple','Smart TV','Unknown'];
  function text(value){return typeof value==='string'?value.slice(0,128):'';}
  function classify(input){
    input=input||{};
    var hostname=text(input.hostname), vendorClass=text(input.vendorClass);
    var mac=text(input.mac), globallyAssigned=/^(?:[0-9a-f]{2}:){5}[0-9a-f]{2}$/i.test(mac)&&!(parseInt(mac.slice(0,2),16)&3);
    var manufacturer=globallyAssigned?text(input.ouiVendor):'';
    var result={category:'Unknown',confidence:'Unknown',manufacturer:manufacturer,os:'',formFactor:'',evidence:[]};
    if(manufacturer)result.evidence.push('Local OUI manufacturer: '+manufacturer);
    var androidName=/(?:^|[-_. ])android(?:$|[-_. ])/i.test(hostname);
    var androidClass=/android/i.test(vendorClass);
    var windowsName=/^(?:desktop|laptop|win)[-_. ]/i.test(hostname);
    var windowsClass=/^(?:MSFT|Microsoft)(?:$|[ ._-])/i.test(vendorClass);
    var television=/(?:^|[-_. ])(?:smart[-_ ]?tv|android[-_ ]?tv|bravia|samsung[-_ ]?tv|lg[-_ ]?tv)(?:$|[-_. ])/i.test(hostname);
    var android=androidName||androidClass,windows=windowsName||windowsClass;
    if(androidName)result.evidence.push('Hostname suggests Android');
    if(androidClass)result.evidence.push('DHCP vendor class suggests Android');
    if(windowsName)result.evidence.push('Hostname suggests Windows');
    if(windowsClass)result.evidence.push('DHCP vendor class suggests Windows');
    if(television){result.formFactor='TV';result.evidence.push('Hostname suggests a television');}
    if(android&&windows){result.confidence='Possible';result.evidence.push('Conflicting OS clues');}
    else if(android){result.os='Android';result.category=television?'Smart TV':'Android';result.confidence=androidName&&androidClass?'High':'Possible';}
    else if(windows){result.os='Windows';result.category=television?'Smart TV':'Windows';result.confidence=windowsName&&windowsClass?'High':'Possible';}
    else if(television){result.category='Smart TV';result.confidence='Possible';}
    else if(/(?:^|[^a-z])Apple(?:[^a-z]|$)/i.test(manufacturer)){result.category='Apple';result.confidence='Manufacturer identified';}
    if(categories.indexOf(input.manualCategory)!==-1){result.category=input.manualCategory;result.confidence='User specified';result.evidence.push('Manual user correction');}
    result.evidence=result.evidence.slice(0,6);
    return result;
  }
  return {classify:classify};
});
