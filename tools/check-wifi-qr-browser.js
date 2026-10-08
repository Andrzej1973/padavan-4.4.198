const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {chromium}=require(process.env.WR_PLAYWRIGHT_MODULE || 'playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:process.env.WR_BROWSER_PATH});
 try {
 const page=await browser.newPage();let requests=0;
 await page.route('**/*',route=>{requests++;return route.abort();});
 let errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.setContent(`<form name="form"><input name="rt_ssid" value="Мережа 🏠"><select name="rt_auth_mode"><option value="psk">WPA2</option><option value="radius">Enterprise</option></select><input name="rt_wep_x" value="0"><input name="rt_wpa_psk" value="пароль123"><input type="radio" name="rt_closed" value="0" checked><input type="radio" name="rt_closed" value="1"><button type="button" id="show">Show</button><button type="button" id="hide">Hide</button></form><p id="wr_wifi_qr_message" data-error="ERROR" data-preview="UNSAVED"></p><div id="wr_wifi_qr" style="display:none;background:white;padding:16px"></div>`);
 for(const name of ['wifi-qrcode-renderer.js','wifi-qr-payload.js','wifi-qr-preview.js'])await page.addScriptTag({content:fs.readFileSync(path.join(__dirname,name),'utf8')});
 await page.evaluate(()=>{document.dispatchEvent(new Event('DOMContentLoaded'));document.getElementById('show').onclick=()=>wrWifiQrShow('rt');document.getElementById('hide').onclick=wrWifiQrHide;});
 await page.click('#show');await page.waitForFunction(()=>document.querySelector('#wr_wifi_qr canvas'));
 assert.equal(await page.locator('#wr_wifi_qr_message').textContent(),'UNSAVED');
 assert.equal(await page.locator('#wr_wifi_qr').getAttribute('title'),null);
 await page.locator('#wr_wifi_qr').screenshot({path:process.argv[2]});
 await page.fill('[name=rt_ssid]','Changed');assert.equal(await page.locator('#wr_wifi_qr').innerHTML(),'');
 await page.click('#show');await page.click('#hide');assert.equal(await page.locator('#wr_wifi_qr').innerHTML(),'');
 await page.selectOption('[name=rt_auth_mode]','radius');await page.click('#show');assert.equal(await page.locator('#wr_wifi_qr_message').textContent(),'ERROR');assert.equal(await page.locator('#wr_wifi_qr').innerHTML(),'');
 assert.deepEqual(errors,[]);assert.equal(requests,0);
 console.log('PASS real Chromium canvas render, clear after editing/hide, unsupported security, no requests or page errors');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exit(1);});
