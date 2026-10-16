const assert=require('node:assert/strict');
let wr_wan_socket_supported=true, original_wan_src_phy='2', shown={};
let select={value:'',options:[]};
let document={form:{wan_src_phy:select,wan_stb_x:{value:'0'},vlan_filter:[{checked:false}]}};
function free_options(s){s.options=[];s.value='';}
function add_option(s,label,value,selected){s.options.push(value);if(selected||s.options.length===1)s.value=value;}
function showhide_div(k,v){shown[k]=v;}
function support_num_ephy(){return 5;}
function change_viptv_tag(){}
const page=require('node:fs').readFileSync(process.argv[2]+'/trunk/user/www/n56u_ribbon_fixed/Advanced_WAN_Content.asp','utf8');
const start=page.indexOf('function change_stb_port_and_vlan(){');
const end=page.indexOf('\nfunction ',start+1);
assert.ok(start>=0 && end>start);
eval(page.slice(start,end));
assert.ok(page.includes("&& !confirm('<#WAN_Socket_Confirm#>')) return;"));
assert.ok(page.includes('id="wr_wan_socket_help"'));
const variables=require('node:fs').readFileSync(process.argv[2]+'/trunk/user/httpd/variables.c','utf8');
assert.ok(variables.includes('{"wan_src_phy", "", NULL, EVM_RESTART_SWITCH_VLAN}'));
for(const file of ['EN.footer','UK.dict','RU.dict']){
 const dict=require('node:fs').readFileSync(process.argv[2]+'/trunk/user/www/dict/'+file,'utf8');
 assert.ok(dict.includes('WAN_Socket_Confirm=') && dict.includes('WAN_Socket_Help='));
}

change_stb_port_and_vlan();
assert.deepEqual(select.options,['0','1','2','3','4']);assert.equal(select.value,'2');assert.equal(shown.wan_src_phy,1);
select.value='4';document.form.wan_stb_x.value='1';change_stb_port_and_vlan();assert.equal(select.value,'4');
wr_wan_socket_supported=false;document.form.wan_stb_x.value='0';change_stb_port_and_vlan();assert.equal(shown.wan_src_phy,false);assert.deepEqual(select.options,['0']);
console.log('PASS WAN selector: IPTV off, all LAN sockets, unsaved selection, legacy model');
