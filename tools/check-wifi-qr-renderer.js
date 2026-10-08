const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'wifi-qrcode-renderer.js'),'utf8');
const begin=source.indexOf('function a(a)');
const end=source.indexOf('function b(',begin);
const c={MODE_8BIT_BYTE:4};
const context={c};vm.createContext(context);vm.runInContext(source.slice(begin,end),context);
for(const value of ['Home','їa','aї','Wi-Fi 🏠','я;密码','\u0080','\u0800']) {
 const data=new context.a(value);
 assert.deepEqual(Array.from(data.parsedData),Array.from(Buffer.from(value,'utf8')));
}
assert.ok(!source.includes('this._el.title=a'));
assert.ok(source.includes('this._el.removeAttribute("title")'));
assert.ok(source.includes('var WRWifiQRCode'));
console.log('PASS: actual QR byte constructor matches UTF-8; no credential title');
