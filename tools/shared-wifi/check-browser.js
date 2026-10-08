const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.WR_PLAYWRIGHT_MODULE||'playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.WR_BROWSER_PATH});
 try{
  const page=await browser.newPage();let requests=0,errors=[];
  await page.route('**/*',r=>{requests++;return r.abort();});page.on('pageerror',e=>errors.push(e.message));
  for(const [band,name] of [['rt','Advanced_Wireless2g_Content.asp'],['wl','Advanced_Wireless_Content.asp']]){
   const source=fs.readFileSync(path.join(process.argv[2],'trunk/user/www/n56u_ribbon_fixed',name),'utf8');
   const marker=source.indexOf('data-wr-shared-choice');assert(marker>0);
   let row=source.slice(source.lastIndexOf('<tr>',marker),source.indexOf('</tr>',marker)+5).replace(/<%[\s\S]*?%>/g,'').replace(/<#.*?#>/g,'Shared Wi-Fi');
   const fields={ssid:'Home',auth_mode:'psk',wep_x:'0',wpa_mode:'2',crypto:'aes',wpa_psk:'password'};
   const inputs=Object.entries(fields).map(([key,value])=>`<input name="${band}_${key}" value="${value}">`).join('');
   await page.setContent(`<form><table>${row}</table>${inputs}<input name="sid_list" value="original"><input name="${band}_channel" value="40"></form>`);
   await page.addScriptTag({content:fs.readFileSync(path.join(__dirname,'ui.js'),'utf8')});
   await page.evaluate(()=>{window.alerts=0;window.alert=()=>window.alerts=(window.alerts||0)+1;});
   async function prepare(){return page.evaluate(band=>{const f=document.querySelector('form');return {ok:WRSharedWifi.prepare(f,band),data:Object.fromEntries(new FormData(f))};},band);}
   let result=await prepare();assert(result.ok);assert(!('wr_wifi_shared' in result.data));assert(!('wr_wifi_source' in result.data));
   assert.equal(result.data.sid_list,band==='rt'?'WLANConfig11b;':'WLANConfig11a;');
   await page.selectOption('[data-wr-shared-choice]','1');result=await prepare();assert(result.ok);
   assert.equal(result.data.wr_wifi_shared,'1');assert.equal(result.data.wr_wifi_source,band);assert.equal(result.data.sid_list,'WLANConfig11b;WLANConfig11a;');assert.equal(result.data[band+'_channel'],'40');
   await page.fill(`[name=${band}_wpa_psk]`,'short');result=await prepare();assert.equal(result.ok,false);assert.equal(await page.evaluate(()=>window.alerts),1);
   await page.evaluate(()=>document.querySelector('[data-wr-shared-choice]').setAttribute('data-current','1'));
   await page.selectOption('[data-wr-shared-choice]','0');result=await prepare();assert(result.ok);assert.equal(result.data.wr_wifi_shared,'0');assert(!('wr_wifi_source' in result.data));assert.equal(result.data.sid_list,'WLANConfig11b;WLANConfig11a;');
  }
  assert.deepEqual(errors,[]);assert.equal(requests,0);
  console.log('PASS real browser actual control rows and FormData both radios: independent omission, shared complete request, invalid password rejection, disable request, independent channel; no network or page errors');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
