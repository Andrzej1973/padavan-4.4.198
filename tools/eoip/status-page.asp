<!DOCTYPE html>
<html><head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<meta http-equiv="Pragma" content="no-cache">
<title><#Web_Title#> - EoIP</title>
<link rel="stylesheet" href="/bootstrap/css/bootstrap.min.css">
<link rel="stylesheet" href="/bootstrap/css/main.css">
<style>
.wr-eoip-editor details {border-top:1px solid #ddd;padding:10px 0}
.wr-eoip-editor summary {cursor:pointer;font-weight:bold}
.wr-eoip-editor fieldset label {display:inline-block;vertical-align:top;width:45%;margin:8px 3% 0 0}
.wr-eoip-editor fieldset input,.wr-eoip-editor fieldset select {display:block;max-width:95%}
.wr-eoip-editor button {margin:4px 6px 4px 0}
</style>
<script src="/jquery.js"></script><script src="/state.js"></script>
<script src="/general.js"></script><script src="/popup.js"></script>
<script src="/help.js"></script><script src="/bootstrap/js/bootstrap.min.js"></script>
<script src="/bootstrap/js/wr-eoip-status.js"></script>
<script src="/bootstrap/js/wr-eoip-editor.js"></script>
<script>
var $j = jQuery.noConflict();
<% login_state_hook(); %>
var wrEoIPLabels = {
 slot:"<#WREOIPSlot#>", state:"<#WREOIPState#>", index:"<#WREOIPIndex#>", master:"<#WREOIPMaster#>",
 unknown:"<#WREOIPUnknown#>", absent:"<#WREOIPAbsent#>", foreign:"<#WREOIPForeign#>",
 up:"<#WREOIPUp#>", down:"<#WREOIPDown#>"
};
function wrEoIPLoad() {
 return new Promise(function(resolve, reject) {
  var attempts=0, deadline=Date.now()+25000;
  function request() {
   if(document.hidden || Date.now()>deadline) { reject(new Error('hidden or expired')); return; }
   $j.ajax({url:'/update.cgi',data:{output:'wr_eoip_status'},dataType:'json',cache:false,timeout:5000})
   .done(function(reply) {
    if(reply && reply.error==='source_unavailable' && reply.pending===true && ++attempts<22) {
     window.setTimeout(request,1000); return;
    }
    resolve(reply);
   }).fail(function(){reject(new Error('unavailable'));});
  }
  request();
 });
}
var wrEoIPRefresh = WREoIPStatus.refresher(wrEoIPLoad,function(rows){
 WREoIPStatus.render(document.getElementById('wr_eoip_observed'),rows,wrEoIPLabels);
});
function initial() {
 show_banner(1); show_menu(5,7,2); show_footer();
 wrEoIPRefresh();
 WREoIPEditor.mount(document.getElementById('wr_eoip_settings_editor'), {
  slot:"<#WREOIPSlot#>",on:"<#checkbox_Yes#>",off:"<#checkbox_No#>",
  masterEnable:"<#WREOIPMasterEnable#>",enable:"<#WREOIPEnable#>",autostart:"<#WREOIPAutostart#>",
  local:"<#WREOIPLocal#>",remote:"<#WREOIPRemote#>",id:"<#WREOIPID#>",mtu:"MTU",
  keepalive:"<#WREOIPKeepalive#>",retries:"<#WREOIPRetries#>",bridge:"<#WREOIPBridge#>",
  confirm:"<#WREOIPConfirm#>",save:"<#WREOIPSave#>",disable:"<#WREOIPDisable#>",reload:"<#WREOIPReload#>",
  unavailable:"<#WREOIPUnavailable#>",loading:"<#WREOIPLoading#>",loaded:"<#WREOIPLoaded#>",
  saving:"<#WREOIPSaving#>",saved:"<#WREOIPSaved#>",rejected:"<#WREOIPRejected#>",uncertain:"<#WREOIPUncertain#>"
 }, {
  read:function(output){return $j.ajax({url:'/update.cgi',data:{output:output},dataType:'json',cache:false,timeout:5000});},
  save:function(payload){return $j.ajax({url:'/wr_eoip_settings.cgi',type:'POST',data:payload,dataType:'json',cache:false,timeout:10000});}
 });
}
</script></head>
<body onload="initial();">
<div class="wrapper">
 <div class="container-fluid"><div class="row-fluid">
  <div class="span3"><div id="logo"></div></div><div class="span9"><div id="TopBanner"></div></div>
 </div></div>
 <div id="Loading" class="popup_bg"></div>
 <form name="form"><input type="hidden" name="current_page" value="Advanced_Services_EoIP.asp"></form>
 <div class="container-fluid"><div class="row-fluid">
  <div class="span3"><div class="well sidebar-nav side_nav" style="padding:0">
   <ul id="mainMenu" class="clearfix"></ul><ul class="clearfix"><li><div id="subMenu" class="accordion"></div></li></ul>
  </div></div>
  <div class="span9"><div class="box well">
   <h2 class="box_head round_top"><#WREOIPTitle#></h2>
   <p class="alert alert-info"><#WREOIPNote#></p>
   <p><#WREOIPReadOnly#></p>
   <div id="wr_eoip_observed" role="status"><#WREOIPUnknown#></div>
   <button type="button" class="btn btn-primary" onclick="wrEoIPRefresh()"><#WREOIPRefresh#></button>
   <a class="btn" href="/Advanced_Services_Content.asp"><#WREOIPBack#></a>
   <hr><h3><#WREOIPSettings#></h3>
   <div id="wr_eoip_settings_editor"></div>
  </div></div>
 </div></div><div id="footer"></div>
</div></body></html>
