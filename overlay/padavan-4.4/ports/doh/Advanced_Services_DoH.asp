<!DOCTYPE html>
<html>
<head>
<title><#Web_Title#> - DoH</title>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<meta http-equiv="Pragma" content="no-cache">
<meta http-equiv="Expires" content="-1">

<link rel="shortcut icon" href="images/favicon.ico">
<link rel="icon" href="images/favicon.png">
<link rel="stylesheet" type="text/css" href="/bootstrap/css/bootstrap.min.css">
<link rel="stylesheet" type="text/css" href="/bootstrap/css/main.css">
<link rel="stylesheet" type="text/css" href="/bootstrap/css/engage.itoggle.css">

<script type="text/javascript" src="/jquery.js"></script>
<script type="text/javascript" src="/bootstrap/js/bootstrap.min.js"></script>
<script type="text/javascript" src="/bootstrap/js/engage.itoggle.min.js"></script>
<script type="text/javascript" src="/state.js"></script>
<script type="text/javascript" src="/general.js"></script>
<script type="text/javascript" src="/itoggle.js"></script>
<script type="text/javascript" src="/popup.js"></script>
<script type="text/javascript" src="/help.js"></script>
<script>
var $j = jQuery.noConflict();
<% login_state_hook(); %>
$j(document).ready(function() { init_itoggle('doh_enable', change_doh_enabled); });
function initial() {
    show_banner(1); show_menu(5,6,2); show_footer(); load_body();
    showhide_div('tbl_anon', found_app_doh());
    change_doh_enabled();
    load_doh_catalog();
}
function change_doh_enabled() {
    var enabled = document.form.doh_enable[0].checked;
    var names = ['doh_server0','doh_server1','doh_server2','doh_server3','doh_bootstrap_dns','doh_listen_port','doh_listen_mode','doh_mode','doh_quic'];
    showhide_div('row_doh_settings', enabled);
    for (var i=0; i<names.length; i++) inputCtrl(document.form[names[i]], enabled && login_safe());
}
function load_doh_catalog() {
    $j.getJSON('/doh.json', function(items) {
        for(var i=0;i<4;i++) {
            var select=document.getElementById('doh_catalog_'+i);
            for(var j=0;j<items.length;j++) {
                if(typeof items[j].url==='string' && items[j].url.indexOf('https://')===0) {
                    var option=new Option(items[j].name,items[j].url);
                    option.selected=(document.form['doh_server'+i].value===items[j].url);
                    select.add(option);
                }
            }
        }
    });
}
function choose_doh(index, value) {
    if(value && login_safe()) document.form['doh_server'+index].value=value;
}
function applyRule() {
    if (!login_safe() || !found_app_doh()) return;
    if (document.form.doh_enable[0].checked) {
        var port = document.form.doh_listen_port.value;
        if (!/^[0-9]{1,5}$/.test(port) || Number(port)<1 || Number(port)>65532) { alert('Listener port must be 1–65532.'); return; }
        var count=0;
        for(var i=0;i<4;i++) { var url=document.form['doh_server'+i].value; if(url) { if(!/^https:\/\/.+/.test(url)) { alert('Use an HTTPS resolver URL.'); return; } count++; } }
        if(!count) { alert('Configure at least one HTTPS resolver.'); return; }
    }
    document.form.action_mode.value = ' Apply ';
    document.form.current_page.value = '/Advanced_Services_DoH.asp';
    document.form.next_page.value = '';
    // The native apply handler reads a fixed 65535-byte encoded POST buffer.
    // Check successful form controls together, including percent encoding.
    if ($j(document.form).serialize().length > 65000) {
        alert('The configuration is too large to save in the web interface. No changes were sent.');
        return;
    }
    showLoading();
    document.form.submit();
}
function done_validating(action) { refreshpage(); }
</script>
</head>
<body onload="initial();" onunLoad="return unload_body();">

<div class="wrapper">
    <div class="container-fluid" style="padding-right: 0px">
        <div class="row-fluid">
            <div class="span3"><center><div id="logo"></div></center></div>
            <div class="span9" >
                <div id="TopBanner"></div>
            </div>
        </div>
    </div>

    <div id="Loading" class="popup_bg"></div>

    <iframe name="hidden_frame" id="hidden_frame" src="" width="0" height="0" frameborder="0"></iframe>
    <form method="post" name="form" id="ruleForm" action="/start_apply.htm" target="hidden_frame">
    <input type="hidden" name="current_page" value="Advanced_Services_DoH.asp">
    <input type="hidden" name="next_page" value="">
    <input type="hidden" name="next_host" value="">
    <input type="hidden" name="sid_list" value="LANHostConfig;General;Storage;">
    <input type="hidden" name="group_id" value="">
    <input type="hidden" name="action_mode" value="">
    <input type="hidden" name="action_script" value="">

    <div class="container-fluid">
        <div class="row-fluid">
            <div class="span3">
                <!--Sidebar content-->
                <!--=====Beginning of Main Menu=====-->
                <div class="well sidebar-nav side_nav" style="padding: 0px;">
                    <ul id="mainMenu" class="clearfix"></ul>
                    <ul class="clearfix">
                        <li>
                            <div id="subMenu" class="accordion"></div>
                        </li>
                    </ul>
                </div>
            </div>

            <div class="span9">
                <!--Body content-->
                <div class="row-fluid">
                    <div class="span12">
                        <div class="box well grad_colour_dark_blue">
                            <h2 class="box_head round_top"><#menu5_6_5#> - DoH</h2>
                            <div class="round_bottom">
                                <div class="row-fluid">
                                    <div id="tabMenu" class="submenuBlock"></div>
                                    <div class="alert alert-info" style="margin: 10px;"><#Adm_Svc_desc#></div>

                                    <table width="100%" cellpadding="4" cellspacing="0" class="table" id="tbl_anon" style="display:none">
                                        <tr>
                                            <th colspan="2" style="background-color: #E3E3E3;">DoH</th>
                                        </tr>

                                        <tr id="row_doh">
                                            <th width="50%">Enable DNS-over-HTTPS</th>
                                            <td>
                                                <div class="main_itoggle">
                                                    <div id="doh_enable_on_of">
                                                        <input type="checkbox" id="doh_enable_fake" <% nvram_match_x("", "doh_enable", "1", "value=1 checked"); %><% nvram_match_x("", "doh_enable", "0", "value=0"); %>>
                                                    </div>
                                                </div>
                                                <div style="position: absolute; margin-left: -10000px;">
                                                    <input type="radio" name="doh_enable" id="doh_enable_1" class="input" value="1" <% nvram_match_x("", "doh_enable", "1", "checked"); %>/><#checkbox_Yes#>
                                                    <input type="radio" name="doh_enable" id="doh_enable_0" class="input" value="0" <% nvram_match_x("", "doh_enable", "0", "checked"); %>/><#checkbox_No#>
                                                </div>
                                            </td>
                                        </tr>
<tr id="row_doh_settings"><td colspan="2"><table class="table"><tr><th>HTTPS resolver 1</th><td><select id="doh_catalog_0" onchange="choose_doh(0, this.value)"><option value="">Custom URL</option></select><input type="text" name="doh_server0" value="<% doh_value("doh_server0"); %>" maxlength="1024" class="span12"></td></tr>
<tr><th>HTTPS resolver 2</th><td><select id="doh_catalog_1" onchange="choose_doh(1, this.value)"><option value="">Custom URL</option></select><input type="text" name="doh_server1" value="<% doh_value("doh_server1"); %>" maxlength="1024" class="span12"></td></tr>
<tr><th>HTTPS resolver 3</th><td><select id="doh_catalog_2" onchange="choose_doh(2, this.value)"><option value="">Custom URL</option></select><input type="text" name="doh_server2" value="<% doh_value("doh_server2"); %>" maxlength="1024" class="span12"></td></tr>
<tr><th>HTTPS resolver 4</th><td><select id="doh_catalog_3" onchange="choose_doh(3, this.value)"><option value="">Custom URL</option></select><input type="text" name="doh_server3" value="<% doh_value("doh_server3"); %>" maxlength="1024" class="span12"></td></tr>
<tr><th>Bootstrap DNS servers</th><td><input type="text" name="doh_bootstrap_dns" value="<% doh_value("doh_bootstrap_dns"); %>" maxlength="1024" class="span12"></td></tr>
<tr><th>First listener port</th><td><input type="text" name="doh_listen_port" value="<% doh_value("doh_listen_port"); %>" maxlength="5" class="span12"></td></tr>
<tr><th>Listener</th><td><select name="doh_listen_mode"><option value="0" <% nvram_match_x("", "doh_listen_mode", "0", "selected"); %>>Loopback</option><option value="1" <% nvram_match_x("", "doh_listen_mode", "1", "selected"); %>>LAN address</option><option value="2" <% nvram_match_x("", "doh_listen_mode", "2", "selected"); %>>All IPv4 addresses</option></select></td></tr>
<tr><th>Mode</th><td><select name="doh_mode"><option value="0" <% nvram_match_x("", "doh_mode", "0", "selected"); %>>Standalone</option><option value="1" <% nvram_match_x("", "doh_mode", "1", "selected"); %>>Use with dnsmasq</option></select></td></tr>
<tr><th>HTTPS transport</th><td><select name="doh_quic"><option value="0" <% nvram_match_x("", "doh_quic", "0", "selected"); %>>HTTP/2</option><option value="1" <% nvram_match_x("", "doh_quic", "1", "selected"); %>>HTTP/3 (QUIC)</option></select></td></tr>
</table></td></tr>
                                    </table>

                                    <table class="table">
                                        <tr>
                                            <td style="border: 0 none;">
                                                <center><input class="btn btn-primary" style="width: 219px" onclick="applyRule();" type="button" value="<#CTL_apply#>" /></center>
                                            </td>
                                        </tr>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    </form>

    <div id="footer"></div>
</div>
</body>
</html>

