// Generate actual QR matrices through the shipped renderer's public constructor.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const make=require('./wifi-qr-payload.js');
function element(){return {children:[],setAttribute(){},setAttributeNS(){},appendChild(x){this.children.push(x);},hasChildNodes(){return this.children.length>0;},removeChild(){this.children.pop();},removeAttribute(){}};}
const context={document:{documentElement:{tagName:'svg'},createElementNS:element},navigator:{userAgent:'QR fixture'},window:{},encodeURIComponent,encodeURI,unescape};
vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'wifi-qrcode-renderer.js'),'utf8'),context);
const base={ssid:'Home',auth:'psk',wep:'0',password:'password',hidden:false};
const cases=[base,{...base,ssid:'Мережа 🏠',password:'пароль123'},{...base,ssid:'a;:,"\\',password:'pass;:,"\\word',hidden:true},{...base,auth:'open',ssid:'Відкрита'},{...base,ssid:'ї'.repeat(16),password:'a'.repeat(63)}];
const output=cases.map((settings,index)=>{const expected=make(settings);if(expected.error)throw Error(expected.error);const qr=new context.WRWifiQRCode(element(),{text:expected.payload,width:240,height:240});return {index,payload:expected.payload,modules:qr._oWRWifiQRCode.modules};});
fs.writeFileSync(process.argv[2],JSON.stringify(output));
console.log('Generated '+output.length+' actual renderer matrices with synthetic credentials');
