/* Shared main-network request planning. No credentials leave this form. */
(function(root){
 "use strict";
 function text(value,min,max){
  if(typeof value!=="string"||/[\x00-\x1f\x7f]/.test(value))return false;
  try {var n=unescape(encodeURIComponent(value)).length;return n>=min&&n<=max;}catch(e){return false;}
 }
 function plan(stored,selected,band,fields){
  if((stored!=="0"&&stored!=="1")||(selected!=="0"&&selected!=="1")||(band!=="rt"&&band!=="wl"))throw new Error("Invalid shared Wi-Fi request");
  if(selected==="0")return {selector:stored==="1"?"0":null,source:null,services:stored==="1"?"WLANConfig11b;WLANConfig11a;":band==="rt"?"WLANConfig11b;":"WLANConfig11a;"};
  if(!fields||!text(fields.ssid,1,32)||fields.wep_x!=="0")throw new Error("Invalid shared Wi-Fi request");
  if(fields.auth_mode!=="open"){
   if(fields.auth_mode!=="psk"||!["0","1","2"].includes(fields.wpa_mode)||!["aes","tkip","tkip+aes"].includes(fields.crypto)||
      !(text(fields.wpa_psk,8,63)||/^[0-9a-fA-F]{64}$/.test(fields.wpa_psk)))throw new Error("Invalid shared Wi-Fi request");
  }
  return {selector:"1",source:band,services:"WLANConfig11b;WLANConfig11a;"};
 }
 function prepare(form,band){
  var choice=form.querySelector("[data-wr-shared-choice]"),names=["ssid","auth_mode","wep_x","wpa_mode","crypto","wpa_psk"],fields={},result;
  if(!choice)return false;
  names.forEach(function(name){var input=form.elements[band+"_"+name];fields[name]=input?input.value:null;});
  try {result=plan(choice.getAttribute("data-current")==="1"?"1":"0",choice.value,band,fields);}catch(e){root.alert(choice.getAttribute("data-error"));return false;}
  form.elements.wr_wifi_shared.disabled=result.selector===null;
  form.elements.wr_wifi_shared.value=result.selector===null?"0":result.selector;
  form.elements.wr_wifi_source.disabled=result.source===null;
  form.elements.wr_wifi_source.value=result.source||band;
  form.elements.sid_list.value=result.services;
  if(result.source)names.forEach(function(name){form.elements[band+"_"+name].disabled=false;});
  return true;
 }
 root.WRSharedWifi={plan:plan,prepare:prepare};
 if(typeof module!=="undefined")module.exports=root.WRSharedWifi;
})(typeof window!=="undefined"?window:globalThis);
