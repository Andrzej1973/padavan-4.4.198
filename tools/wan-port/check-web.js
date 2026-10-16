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
const status=require('node:fs').readFileSync(process.argv[2]+'/trunk/user/httpd/web_ex.c','utf8');
assert.ok(status.includes('int eth_link = fill_eth_port_status(0, etherlink);'));
for(const file of ['EN.footer','UK.dict','RU.dict']){
 const dict=require('node:fs').readFileSync(process.argv[2]+'/trunk/user/www/dict/'+file,'utf8');
 assert.ok(dict.includes('WAN_Socket_Confirm=') && dict.includes('WAN_Socket_Help='));
}

change_stb_port_and_vlan();
assert.deepEqual(select.options,['0','1','2','3','4']);assert.equal(select.value,'2');assert.equal(shown.wan_src_phy,1);
select.value='4';document.form.wan_stb_x.value='1';change_stb_port_and_vlan();assert.equal(select.value,'4');
wr_wan_socket_supported=false;document.form.wan_stb_x.value='0';change_stb_port_and_vlan();assert.equal(shown.wan_src_phy,false);assert.deepEqual(select.options,['0']);
console.log('PASS WAN selector: IPTV off, all LAN sockets, unsaved selection, legacy model');

let confirmations=0, submissions=0, loading=0, accepted=false;
function validForm(){return true;}
function confirm(){confirmations++;return accepted;}
function showLoading(){loading++;}
document.form.pppoemwan_rules_x=[{checked:false}];
for(const key of ['action_mode','current_page','next_page']) document.form[key]={value:''};
document.form.submit=()=>{submissions++;};
const applyStart=page.indexOf('function applyRule(){');
const applyEnd=page.indexOf('\nfunction ',applyStart+1);
eval(page.slice(applyStart,applyEnd));
wr_wan_socket_supported=true;select.value='4';
applyRule();assert.equal(confirmations,1);assert.equal(submissions,0);assert.equal(loading,0);
accepted=true;applyRule();assert.equal(submissions,1);assert.equal(loading,1);
select.value=original_wan_src_phy;applyRule();assert.equal(confirmations,2);assert.equal(submissions,2);
select.value='0';accepted=false;applyRule();assert.equal(confirmations,3);assert.equal(submissions,2);
console.log('PASS WAN Apply: cancel, accept, unchanged selection, restore confirmation');
