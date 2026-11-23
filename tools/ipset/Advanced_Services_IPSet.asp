<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>IPSet</title>
<link rel="stylesheet" href="/bootstrap/css/bootstrap.min.css">
<link rel="stylesheet" href="/bootstrap/css/main.css">
<script src="/jquery.js"></script>
<script src="/bootstrap/js/bootstrap.min.js"></script>
<script src="/state.js"></script>
<script src="/popup.js"></script>
<script>
function showIPSetState() {
    var states = ['<#WRIPSetDisabled#>', '<#WRIPSetRunning#>', '<#WRIPSetStopped#>'];
    document.getElementById('ipset_status').textContent = states[<% wr_classic_ipset_state(); %>];
    var results = ['<#WRIPSetNoResult#>', '<#WRIPSetUpdated#>', '<#WRIPSetError#>', '<#WRIPSetUnconfigured#>'];
    var last = <% wr_classic_ipset_result(); %>;
    var text = results[last[0]];
    if (last[0] === 1 || last[0] === 2) {
        text += ' · <#WRIPSetSucceededCount#> ' + last[1] + ' · <#WRIPSetFailedCount#> ' + last[2];
    }
    document.getElementById('ipset_result').textContent = text;
}
function done_validating() { location.reload(); }
</script>
</head>
<body onload="show_banner(1); show_menu(5,7,2); show_footer(); showIPSetState();">
<div class="wrapper">
    <div class="container-fluid">
        <div class="row-fluid">
            <div class="span3"><div id="logo"></div></div>
            <div class="span9"><div id="TopBanner"></div></div>
        </div>
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
                    <h2>IPSet</h2>
                    <p><#WRIPSetStatus#> <strong id="ipset_status" role="status">—</strong></p>
                    <p><#WRIPSetLastRefresh#> <strong id="ipset_result">—</strong></p>
                    <iframe name="hidden_frame" title="Apply" hidden></iframe>
                    <form method="post" action="/start_apply.htm" target="hidden_frame" name="form">
                        <input type="hidden" name="action_mode" value=" Apply ">
                        <input type="hidden" name="current_page" value="/Advanced_Services_IPSet.asp">
                        <input type="hidden" name="next_page" value="">
                        <input type="hidden" name="next_host" value="">
                        <input type="hidden" name="action_script" value="">
                        <input type="hidden" name="group_id" value="">
                        <input type="hidden" name="sid_list" value="LANHostConfig;">
                        <table class="table">
                            <tr><th><label for="ipset_enable"><#WRIPSetEnable#></label></th>
                                <td><select id="ipset_enable" name="wr_classic_ipset_enable">
                                    <option value="0" <% nvram_match_x("", "wr_classic_ipset_enable", "0", "selected"); %>><#checkbox_No#></option>
                                    <option value="1" <% nvram_match_x("", "wr_classic_ipset_enable", "1", "selected"); %>><#checkbox_Yes#></option>
                                </select></td></tr>
                            <tr><th><label for="ipset_period"><#WRIPSetPeriod#></label></th>
                                <td><select id="ipset_period" name="wr_classic_ipset_period">
                                    <!-- IPSET_PERIOD_OPTIONS -->
                                </select></td></tr>
                            <tr><th><label for="ipset_feeds"><#WRIPSetFeeds#></label></th>
                                <td><textarea id="ipset_feeds" class="span12" rows="8" maxlength="8192" spellcheck="false" name="scripts.wr-classic-ipset.feeds"><% nvram_dump("scripts.wr-classic-ipset.feeds",""); %></textarea>
                                    <p class="help-block"><#WRIPSetFeedsHelp#></p></td></tr>
                        </table>
                        <button class="btn btn-primary" type="submit"><#CTL_apply#></button>
                    </form>
                </div>
            </main>
        </div>
    </div>
    <div id="footer"></div>
</div>
</body>
</html>
