(function(){
 'use strict';
 function boot(){var root=document.getElementById('wr-connected-devices');if(!root)return;
  var page=WRDeviceHomepage.mount(document,root,WRDeviceRefresh);
  var historyRoot=document.getElementById('wr-roaming-history'),history=historyRoot?WRRoamingView.mount(document,historyRoot,WRDeviceRefresh,WRRoaming):null;
  var rssiRoot=document.getElementById('wr-rssi-history'),rssi=rssiRoot?WRRssiView.mount(document,rssiRoot,WRDeviceRefresh,WRRssi):null;
  window.addEventListener('unload',function(){page.stop();if(history)history.stop();if(rssi)rssi.stop();});
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
