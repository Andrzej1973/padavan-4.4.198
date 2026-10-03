<!DOCTYPE html>
<html>
<head>
<title><#Web_Title#> - Privoxy</title>
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
$j(document).ready(function() { init_itoggle('privoxy_enable', change_privoxy_enabled); });
function initial() {
    show_banner(1); show_menu(5,6,2); show_footer(); load_body();
    showhide_div('tbl_anon', found_app_privoxy());
    change_privoxy_enabled();
}
function change_privoxy_enabled() {
    var enabled = document.form.privoxy_enable[0].checked;
    var names = ['config', 'user.action', 'user.filter', 'user.trust'];
    var rows = ['conf', 'action', 'filter', 'trust'];
    for (var i = 0; i < names.length; i++) {
        showhide_div('row_privoxy_' + rows[i], enabled);
        inputCtrl(document.form['privoxy.' + names[i]], enabled && login_safe());
    }
}
function applyRule() {
    if (!login_safe() || !found_app_privoxy()) return;
    document.form.action_mode.value = ' Apply ';
    document.form.current_page.value = '/Advanced_Services_Privoxy.asp';
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
    <input type="hidden" name="current_page" value="Advanced_Services_Privoxy.asp">
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
                            <h2 class="box_head round_top"><#menu5_6_5#> - Privoxy</h2>
                            <div class="round_bottom">
                                <div class="row-fluid">
                                    <div id="tabMenu" class="submenuBlock"></div>
                                    <div class="alert alert-info" style="margin: 10px;"><#Adm_Svc_desc#></div>

                                    <table width="100%" cellpadding="4" cellspacing="0" class="table" id="tbl_anon" style="display:none">
                                        <tr>
                                            <th colspan="2" style="background-color: #E3E3E3;">Privoxy</th>
                                        </tr>

                                        <tr id="row_privoxy">
                                            <th width="50%"><#Adm_Svc_privoxy#></th>
                                            <td>
                                                <div class="main_itoggle">
                                                    <div id="privoxy_enable_on_of">
                                                        <input type="checkbox" id="privoxy_enable_fake" <% nvram_match_x("", "privoxy_enable", "1", "value=1 checked"); %><% nvram_match_x("", "privoxy_enable", "0", "value=0"); %>>
                                                    </div>
                                                </div>
                                                <div style="position: absolute; margin-left: -10000px;">
                                                    <input type="radio" name="privoxy_enable" id="privoxy_enable_1" class="input" value="1" <% nvram_match_x("", "privoxy_enable", "1", "checked"); %>/><#checkbox_Yes#>
                                                    <input type="radio" name="privoxy_enable" id="privoxy_enable_0" class="input" value="0" <% nvram_match_x("", "privoxy_enable", "0", "checked"); %>/><#checkbox_No#>
                                                </div>
                                            </td>
                                        </tr>
                                        <tr id="row_privoxy_conf" style="display:none">
                                            <td colspan="2">
                                                <a href="javascript:spoiler_toggle('spoiler_privoxy_conf')"><span><#CustomConf#> "config"</span></a>
                                                <div id="spoiler_privoxy_conf" style="display:none;">
                                                    <textarea rows="16" wrap="off" spellcheck="false" class="span12" name="privoxy.config" style="font-family:'Courier New'; font-size:12px; resize:vertical;"><% nvram_dump("privoxy.config",""); %></textarea>
                                                </div>
                                            </td>
                                        </tr>
                                        <tr id="row_privoxy_action" style="display:none">
                                            <td colspan="2">
                                                <a href="javascript:spoiler_toggle('spoiler_privoxy_action')"><span><#CustomConf#> "user.action"</span></a>
                                                <div id="spoiler_privoxy_action" style="display:none;">
                                                    <textarea rows="16" wrap="off" spellcheck="false" class="span12" name="privoxy.user.action" style="font-family:'Courier New'; font-size:12px; resize:vertical;"><% nvram_dump("privoxy.user.action",""); %></textarea>
                                                </div>
                                            </td>
                                        </tr>
                                        <tr id="row_privoxy_filter" style="display:none">
                                            <td colspan="2">
                                                <a href="javascript:spoiler_toggle('spoiler_privoxy_filter')"><span><#CustomConf#> "user.filter"</span></a>
                                                <div id="spoiler_privoxy_filter" style="display:none;">
                                                    <textarea rows="16" wrap="off" spellcheck="false" class="span12" name="privoxy.user.filter" style="font-family:'Courier New'; font-size:12px; resize:vertical;"><% nvram_dump("privoxy.user.filter",""); %></textarea>
                                                </div>
                                            </td>
                                        </tr>
                                        <tr id="row_privoxy_trust" style="display:none">
                                            <td colspan="2">
                                                <a href="javascript:spoiler_toggle('spoiler_privoxy_trust')"><span><#CustomConf#> "user.trust"</span></a>
                                                <div id="spoiler_privoxy_trust" style="display:none;">
                                                    <textarea rows="16" wrap="off" spellcheck="false" class="span12" name="privoxy.user.trust" style="font-family:'Courier New'; font-size:12px; resize:vertical;"><% nvram_dump("privoxy.user.trust",""); %></textarea>
                                                </div>
                                            </td>
                                        </tr>
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
