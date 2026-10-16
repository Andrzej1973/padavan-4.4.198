const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
function element(){return {children:[],setAttribute(){},setAttributeNS(){},appendChild(x){this.children.push(x);},hasChildNodes(){return this.children.length>0;},removeChild(){this.children.pop();},removeAttribute(){}};}
const context={document:{documentElement:{tagName:'svg'},createElementNS:element},navigator:{userAgent:'synthetic VPN QR'},window:{},encodeURIComponent,encodeURI,unescape};
vm.createContext(context);vm.runInContext(fs.readFileSync(path.join(__dirname,'wifi-qrcode-renderer.js'),'utf8'),context);
const base='[Interface]\nPrivateKey = '+'A'.repeat(43)+'=\nAddress = 10.0.0.2/32\n\n[Peer]\nPublicKey = '+'B'.repeat(43)+'=\nEndpoint = example.invalid:51820\nAllowedIPs = 10.0.0.0/24\n';
const awg=base.replace('Address =','Jc = 4\nJmin = 40\nJmax = 70\nS1 = 10\nS2 = 20\nH1 = 123\nH2 = 456\nH3 = 789\nH4 = 987\nAddress =');
const cases=[base,awg,'# Тестовий профіль — приватні ключі тут синтетичні\n'+awg];
const output=cases.map((payload,index)=>{const qr=new context.WRWifiQRCode(element(),{text:payload,width:256,height:256});return {index,payload,modules:qr._oWRWifiQRCode.modules};});
fs.writeFileSync(process.argv[2],JSON.stringify(output));console.log('Generated synthetic WG/AWG/UTF-8 matrices from actual renderer');
