"use strict";
const assert=require("assert");const ui=require("./ui.js");
const fields={ssid:"Home",auth_mode:"psk",wep_x:"0",wpa_mode:"2",crypto:"aes",wpa_psk:"password"};
assert.strictEqual(ui.plan("0","0","rt",{}).selector,null);
assert.strictEqual(ui.plan("0","0","wl",{}).services,"WLANConfig11a;");
assert.strictEqual(ui.plan("1","0","rt",{}).selector,"0");
for(const band of ["rt","wl"]){const p=ui.plan("0","1",band,fields);assert.strictEqual(p.source,band);assert.strictEqual(p.services,"WLANConfig11b;WLANConfig11a;");}
assert.throws(()=>ui.plan("0","1","rt",{...fields,wpa_psk:"short"}));
assert.throws(()=>ui.plan("0","1","rt",{...fields,auth_mode:"wpa2"}));
assert.throws(()=>ui.plan("0","1","rt",{...fields,ssid:"a".repeat(33)}));
assert.throws(()=>ui.plan("0","1","rt",{...fields,ssid:"\ud800"}));
assert.throws(()=>ui.plan("0","1","rt",{...fields,wep_x:"1"}));
assert.strictEqual(ui.plan("0","1","rt",{...fields,wpa_psk:"a".repeat(64)}).selector,"1");
assert.throws(()=>ui.plan("0","1","rt",{...fields,wpa_psk:"z".repeat(64)}));
assert.strictEqual(ui.plan("0","1","rt",{ssid:"Open",auth_mode:"open",wep_x:"0"}).selector,"1");
console.log("PASS shared Wi-Fi UI request planning: independent default, both sources, disable preservation request, UTF-8 bounds, security, raw PSK");

for(const band of ["rt","wl"]){
 const choice={value:"1",getAttribute:key=>key==="data-current"?"0":"Invalid"};
 const elements={wr_wifi_shared:{},wr_wifi_source:{},sid_list:{value:"original"}};
 for(const [key,value] of Object.entries(fields))elements[band+"_"+key]={value,disabled:true};
 const form={elements,querySelector:()=>choice};
 assert.strictEqual(ui.prepare(form,band),true);
 assert.strictEqual(elements.wr_wifi_shared.value,"1");assert.strictEqual(elements.wr_wifi_source.value,band);
 assert.strictEqual(elements.sid_list.value,"WLANConfig11b;WLANConfig11a;");
 assert.strictEqual(elements[band+"_ssid"].disabled,false);
 choice.value="0";assert.strictEqual(ui.prepare(form,band),true);
 assert.strictEqual(elements.wr_wifi_shared.disabled,true);assert.strictEqual(elements.wr_wifi_source.disabled,true);
 assert.strictEqual(elements.sid_list.value,band==="rt"?"WLANConfig11b;":"WLANConfig11a;");
}
console.log("PASS actual form adapter both bands: explicit selector submission, enabled security fields, independent services restored");
