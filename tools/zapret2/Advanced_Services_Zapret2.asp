<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title><#WRZapret2Title#></title>
<link rel="stylesheet" href="/bootstrap/css/bootstrap.min.css">
<link rel="stylesheet" href="/bootstrap/css/main.css">
<link rel="stylesheet" href="/bootstrap/css/engage.itoggle.css">
<script src="/jquery.js"></script>
<script src="/bootstrap/js/bootstrap.min.js"></script>
<script src="/bootstrap/js/engage.itoggle.min.js"></script>
<script src="/state.js"></script>
<script src="/general.js"></script>
<script src="/itoggle.js"></script>
<script src="/popup.js"></script>
<script>
var $j = jQuery.noConflict();
function initial(){
    show_banner(1); show_menu(5,7,2); show_footer(); load_body();
    if(!found_app_zapret2()) {
        showhide_div('zapret2_settings', 0);
        return;
    }
    init_itoggle('zapret2_enable');
    wrZapret2Render(<% wr_zapret2_status(); %>);
    window.setInterval(wrZapret2Refresh, 30000);
}
// ZAPRET2_STATUS_SCRIPT
function applyRule(){
    if(found_app_zapret2() && validZapret2()){
        var form = document.form;
        var unchanged = $j(form).find('[data-zapret2-profile] textarea, textarea[data-zapret2-file]').filter(function () {
            return this.value === this.defaultValue;
        });
        form.action_mode.value = " Apply ";
        unchanged.prop('disabled', true);
        try {
            // Padavan httpd reads at most 65534 bytes of the encoded POST body.
            if ($j(form).serialize().length > 65000) {
                alert('<#WRZapret2RequestTooLarge#>');
                return;
            }
            showLoading();
            form.submit();
        } finally {
            unchanged.prop('disabled', false);
        }
    }
}
function done_validating(action){ refreshpage(); }
</script>
</head>
<body onload="initial();" onunload="return unload_body();">
<div class="wrapper">
    <div class="container-fluid">
        <div class="row-fluid">
            <div class="span3"><div id="logo"></div></div>
            <div class="span9"><div id="TopBanner"></div></div>
        </div>
    </div>
    <div id="Loading" class="popup_bg"></div>
    <iframe name="hidden_frame" id="hidden_frame" src="" width="0" height="0" frameborder="0"></iframe>
    <div class="container-fluid">
        <div class="row-fluid">
            <div class="span3">
                <div class="well sidebar-nav side_nav">
                    <ul id="mainMenu" class="clearfix"></ul>
                    <ul class="clearfix"><li><div id="subMenu" class="accordion"></div></li></ul>
                </div>
            </div>
            <main class="span9">
                <div class="well">
                    <div id="tabMenu" class="submenuBlock"></div>
                    <h2><#WRZapret2Title#></h2>
                    <form method="post" name="form" id="zapret2_settings" action="/start_apply.htm" target="hidden_frame">
                        <input type="hidden" name="current_page" value="/Advanced_Services_Zapret2.asp">
                        <input type="hidden" name="next_page" value="">
                        <input type="hidden" name="next_host" value="">
                        <input type="hidden" name="sid_list" value="LANHostConfig;General;Storage;">
                        <input type="hidden" name="group_id" value="">
                        <input type="hidden" name="action_mode" value="">
                        <input type="hidden" name="action_script" value="">
                        <table class="table"><tbody>
                            <!-- ZAPRET2_ROWS -->
                        </tbody></table>
                        <button type="button" class="btn btn-primary" onclick="applyRule();"><#CTL_apply#></button>
                    </form>
                </div>
            </main>
        </div>
    </div>
    <div id="footer"></div>
</div>
</body>
</html>
