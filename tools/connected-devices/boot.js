(function(){
 'use strict';
 function boot(){var root=document.getElementById('wr-connected-devices');if(!root)return;
  var nav=document.getElementById('wr-observation-launcher'),historyRoot=document.getElementById('wr-roaming-history'),rssiRoot=document.getElementById('wr-rssi-history');
  var views={devices:root,history:historyRoot,rssi:rssiRoot},match=/(?:^|[?&])wr_view=(devices|history|rssi)(?:&|$)/.exec(window.location.search),active=match&&views[match[1]];
  var mounted=null;
  if(active){
   var page=document.createElement('main'),back=document.createElement('a');page.id='wr-observation-detail';
   back.className='wr-observation-back';back.href='/';back.textContent='← '+(active.getAttribute('data-wr-back')||'Back');back.addEventListener('click',function(event){if(window.history.length>1){event.preventDefault();window.history.back();}});page.appendChild(back);
   var home=document.createElement('a');home.className='wr-observation-home';home.href='/';home.textContent=active.getAttribute('data-wr-home')||'Home';page.appendChild(home);
   active.style.display='block';page.appendChild(active);document.body.appendChild(page);
   for(var i=0;i<document.body.children.length;i++)if(document.body.children[i]!==page)document.body.children[i].style.display='none';
   mounted=active===root?WRDeviceHomepage.mount(document,root,WRDeviceRefresh):active===historyRoot?WRRoamingView.mount(document,historyRoot,WRDeviceRefresh,WRRoaming):WRRssiView.mount(document,rssiRoot,WRDeviceRefresh,WRRssi);
  }else{
   if(nav)nav.style.display='';root.style.display='none';if(historyRoot)historyRoot.style.display='none';if(rssiRoot)rssiRoot.style.display='none';
  }
  if(mounted)window.addEventListener('unload',function(){mounted.stop();});
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',boot);else boot();
})();
