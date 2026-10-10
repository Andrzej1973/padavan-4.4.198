(function(){
 'use strict';
 function boot(){var root=document.getElementById('wr-connected-devices');if(!root)return;
  var page=WRDeviceHomepage.mount(document,root,WRDeviceRefresh);
  var historyRoot=document.getElementById('wr-roaming-history'),history=historyRoot?WRRoamingView.mount(document,historyRoot,WRDeviceRefresh,WRRoaming):null;
  window.addEventListener('unload',function(){page.stop();if(history)history.stop();});
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
