/* Full prepared DOM check with legacy scripts/server rendering excluded. */
const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.WR_PLAYWRIGHT_MODULE||'playwright');
(async()=>{const browser=await chromium.launch({headless:true,executablePath:process.env.WR_BROWSER_PATH});try{
 const page=await browser.newPage();let errors=[];page.on('pageerror',e=>errors.push(e.message));await page.route('**/*',r=>r.abort());
 for(const [band,name] of [['rt','Advanced_Wireless2g_Content.asp'],['wl','Advanced_Wireless_Content.asp']]){
  let html=fs.readFileSync(path.join(process.argv[2],'trunk/user/www/n56u_ribbon_fixed',name),'utf8');
  html=html.replace(/<%[\s\S]*?%>/g,'').replace(/<#.*?#>/g,'Label').replace(/<script\b[\s\S]*?<\/script>/gi,'').replace(/<link\b[^>]*>/gi,'').replace(/<img\b[^>]*>/gi,'').replace(/\s+onload="[^"]*"/gi,'');
  await page.setContent(html);await page.addScriptTag({content:fs.readFileSync(path.join(__dirname,'ui.js'),'utf8')});
  const result=await page.evaluate(band=>{
   const f=document.querySelector('form[name="form"]');WRSharedWifi.initAdvanced();
   const channel=f.elements[band+'_channel'],ssid=f.elements[band+'_ssid'],time=f.elements[band+'_radio_time_x_starthour'];
   const button=f.querySelector('[onclick="WRSharedWifi.advanced(this)"]');
   if(!channel.closest('tr').hidden||!time.closest('tr').hidden||ssid.closest('tr').hidden)throw Error('Wrong initial row grouping');
   const before=JSON.stringify(Array.from(new FormData(f))),style=channel.closest('tr').getAttribute('style');
   WRSharedWifi.advanced(button);
   if(channel.closest('tr').hidden||time.closest('tr').hidden||button.getAttribute('aria-expanded')!=='true')throw Error('Expand failed');
   if(JSON.stringify(Array.from(new FormData(f)))!==before)throw Error('Fields changed');
   channel.closest('tr').style.display='none';WRSharedWifi.advanced(button);WRSharedWifi.advanced(button);
   if(channel.closest('tr').style.display!=='none')throw Error('Existing dynamic visibility overwritten');
   channel.closest('tr').setAttribute('style',style||'');
   return {rows:f.querySelectorAll('[data-wr-advanced]').length};
  },band);
  assert(result.rows>=10);
 }
 assert.deepEqual(errors,[]);console.log('PASS full prepared DOM both radios: channels and schedules collapse, SSID remains visible, FormData unchanged, existing display state preserved; legacy scripts not exercised');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exit(1);});
