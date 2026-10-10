(function(){
 'use strict';
 function boot(){var root=document.getElementById('wr-connected-devices');if(!root)return;
  var page=WRDeviceHomepage.mount(document,root,WRDeviceRefresh);
  window.addEventListener('unload',function(){page.stop();});
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
