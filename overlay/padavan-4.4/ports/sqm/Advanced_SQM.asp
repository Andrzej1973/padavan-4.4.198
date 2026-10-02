<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8">
<meta http-equiv="Pragma" content="no-cache">
<title><#Web_Title#> - CAKE SQM</title>
<link rel="stylesheet" href="/bootstrap/css/bootstrap.min.css">
<link rel="stylesheet" href="/bootstrap/css/main.css">
<script src="/jquery.js"></script>
<script src="/state.js"></script>
<script src="/general.js"></script>
<script src="/popup.js"></script>
<script>
function initial() {
    show_banner(2);
    show_menu(5, 19);
    show_footer();
}
function validateCakeRate(value) {
    if (!/^[0-9]{1,7}$/.test(value)) return null;
    var rate = Number(value);
    return rate <= 2000000 ? rate : null;
}
function applyRule() {
    var form = document.form;
    if (document.getElementById('sqm_enable_1').checked) {
        var down = validateCakeRate(form.sqm_down_speed.value);
        var up = validateCakeRate(form.sqm_up_speed.value);
        if (down === null || up === null || (down === 0 && up === 0)) {
            alert('<#SQM_CAKE_InvalidRate#>');
            return false;
        }
    }
    showLoading();
    form.action_mode.value = ' Restart ';
    form.current_page.value = 'Advanced_SQM.asp';
    form.next_page.value = '';
    form.submit();
    return true;
}
function done_validating(action) { refreshpage(); }
</script>
</head>
<body onload="initial();" onunload="return unload_body();">
<div class="wrapper">
<div class="container-fluid"><div class="row-fluid">
<div class="span3"><div id="logo"></div></div>
<div class="span9"><div id="TopBanner"></div></div>
</div></div>
<div id="Loading" class="popup_bg"></div>
<iframe name="hidden_frame" id="hidden_frame" src="" width="0" height="0" frameborder="0"></iframe>
<form name="form" method="post" action="/start_apply.htm" target="hidden_frame">
<input type="hidden" name="current_page" value="Advanced_SQM.asp">
<input type="hidden" name="next_page" value="">
<input type="hidden" name="next_host" value="">
<input type="hidden" name="sid_list" value="SqmConf;">
<input type="hidden" name="group_id" value="">
<input type="hidden" name="action_mode" value="">
<input type="hidden" name="action_script" value="">
<div class="container-fluid"><div class="row-fluid">
<div class="span3"><div class="well sidebar-nav side_nav" style="padding:0">
<ul id="mainMenu" class="clearfix"></ul>
<ul class="clearfix"><li><div id="subMenu" class="accordion"></div></li></ul>
</div></div>
<div class="span9"><div class="box well grad_colour_dark_blue">
<h2 class="box_head round_top">CAKE SQM</h2>
<div class="round_bottom">
<div class="alert alert-info"><#SQM_CAKE_Description#></div>
<table class="table">
<tr><th><#SQM_CAKE_Enable#></th><td>
<label class="radio inline"><input type="radio" name="sqm_enable" id="sqm_enable_1" value="1" <% nvram_match_x("", "sqm_enable", "1", "checked"); %>><#SQM_CAKE_On#></label>
<label class="radio inline"><input type="radio" name="sqm_enable" id="sqm_enable_0" value="0" <% nvram_match_x("", "sqm_enable", "0", "checked"); %>><#SQM_CAKE_Off#></label>
</td></tr>
<tr><th><label for="sqm_down_speed"><#SQM_CAKE_Download#></label></th><td>
<input type="text" id="sqm_down_speed" name="sqm_down_speed" maxlength="7" value="<% nvram_get_x("", "sqm_down_speed"); %>"> kbit/s
</td></tr>
<tr><th><label for="sqm_up_speed"><#SQM_CAKE_Upload#></label></th><td>
<input type="text" id="sqm_up_speed" name="sqm_up_speed" maxlength="7" value="<% nvram_get_x("", "sqm_up_speed"); %>"> kbit/s
</td></tr>
</table>
<p><#SQM_CAKE_RateHelp#></p>
<p><#SQM_CAKE_Performance#></p>
<div style="text-align:center;padding:12px">
<input type="button" class="btn btn-primary" value="<#CTL_apply#>" onclick="applyRule();">
</div>
</div></div></div>
</div></div>
</form>
<div id="footer"></div>
</div>
</body>
</html>
