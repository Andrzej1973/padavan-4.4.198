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
    var status = document.getElementById('ipset_status');
    status.textContent = states[parseInt(status.dataset.state, 10)] || '—';
    var results = ['<#WRIPSetNoResult#>', '<#WRIPSetUpdated#>', '<#WRIPSetError#>', '<#WRIPSetUnconfigured#>'];
    var result = document.getElementById('ipset_result');
    var last = JSON.parse(result.dataset.result || '[0,0,0]');
    var text = results[last[0]];
    if (last[0] === 1 || last[0] === 2) {
        text += ' · <#WRIPSetSucceededCount#> ' + last[1] + ' · <#WRIPSetFailedCount#> ' + last[2];
    }
    result.textContent = text;
}
function initIPSetFeeds() {
    var feeds = document.getElementById('ipset_feeds');
    var rows = document.getElementById('ipset_rows');
    var report = document.getElementById('ipset_file_status');
    function current() {
        return feeds.value.split(/\r?\n/).filter(function (line) {
            return line.trim() && !/^\s*#/.test(line);
        }).map(function (line) { return line.trim().split(/\s+/); });
    }
    function render() {
        rows.textContent = '';
        var lines = feeds.value.split(/\r?\n/);
        lines.forEach(function (line, index) {
            if (!line.trim() || /^\s*#/.test(line)) return;
            var pair = line.trim().split(/\s+/);
            var row = rows.insertRow();
            row.insertCell().textContent = pair[0];
            row.insertCell().textContent = pair.slice(1).join(' ');
            var remove = document.createElement('button');
            remove.type = 'button';
            remove.className = 'btn btn-mini';
            remove.textContent = '<#WRIPSetRemove#>';
            remove.addEventListener('click', function () {
                lines.splice(index, 1);
                feeds.value = lines.join('\n');
                render();
            });
            row.insertCell().appendChild(remove);
        });
    }
    feeds.addEventListener('input', render);
    document.getElementById('ipset_add').addEventListener('click', function () {
        var name = document.getElementById('ipset_name');
        var url = document.getElementById('ipset_url');
        var setName = name.value.trim();
        var sourceUrl = url.value.trim();
        var entries = current();
        var source = feeds.value.trimEnd();
        source += (source ? '\n' : '') + setName + ' ' + sourceUrl;
        if (!/^[A-Za-z0-9_]{1,20}$/.test(setName) || setName === 'zapret2_clients' ||
            !/^https:\/\/[^\s\x00-\x1f\x7f]+$/.test(sourceUrl) ||
            entries.length >= 16 || entries.some(function (pair) { return pair[0] === setName; }) ||
            new Blob([source]).size > 8192) {
            report.textContent = '<#WRIPSetAddError#>';
            return;
        }
        feeds.value = source;
        name.value = '';
        url.value = '';
        report.textContent = '';
        render();
        name.focus();
    });
    document.getElementById('ipset_import').addEventListener('change', function () {
        var input = this;
        var file = input.files[0];
        input.value = '';
        if (!file) return;
        var reader = new FileReader();
        function reject() { report.textContent = '<#WRIPSetImportError#>'; }
        if (file.size > 32768) { reject(); return; }
        reader.onerror = reject;
        reader.onload = function () {
            try {
                var entries = JSON.parse(reader.result);
                var names = Object.create(null);
                if (!Array.isArray(entries) || entries.length > 16) throw new Error();
                var source = entries.map(function (entry) {
                    if (!entry || typeof entry.name !== 'string' || typeof entry.url !== 'string' ||
                        !/^[A-Za-z0-9_]{1,20}$/.test(entry.name) || entry.name === 'zapret2_clients' ||
                        names[entry.name] || !/^https:\/\/[^\s\x00-\x1f\x7f]+$/.test(entry.url)) throw new Error();
                    names[entry.name] = true;
                    return entry.name + ' ' + entry.url;
                }).join('\n');
                if (new Blob([source]).size > 8192) throw new Error();
                feeds.value = source;
                render();
                report.textContent = '<#WRIPSetImported#>';
            } catch (error) { reject(); }
        };
        reader.readAsText(file);
    });
    document.getElementById('ipset_export').addEventListener('click', function () {
        var entries = current().map(function (pair) { return {name: pair[0], url: pair.slice(1).join(' ')}; });
        var url = URL.createObjectURL(new Blob([JSON.stringify(entries, null, 2)], {type: 'application/json'}));
        var link = document.createElement('a');
        link.href = url;
        link.download = 'padavan-classic-ipset.json';
        link.click();
        setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
    });
    render();
}
document.addEventListener('DOMContentLoaded', function () {
    initIPSetFeeds();
    showIPSetState();
});
function done_validating() { location.reload(); }
</script>
</head>
<body onload="show_banner(1); show_menu(5,7,2); show_footer();">
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
                    <p><#WRIPSetStatus#> <strong id="ipset_status" role="status" data-state="<% wr_classic_ipset_state(); %>">—</strong></p>
                    <p><#WRIPSetLastRefresh#> <strong id="ipset_result" data-result="<% wr_classic_ipset_result(); %>">—</strong></p>
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
                                    <p class="help-block"><#WRIPSetFeedsHelp#></p>
                                    <table class="table table-condensed"><thead><tr><th>IPSet</th><th>HTTPS</th><th></th></tr></thead><tbody id="ipset_rows"></tbody></table>
                                    <label for="ipset_name"><#WRIPSetName#></label>
                                    <input type="text" id="ipset_name" maxlength="20">
                                    <label for="ipset_url">HTTPS</label>
                                    <input type="url" id="ipset_url" class="span12">
                                    <button type="button" id="ipset_add" class="btn"><#WRIPSetAdd#></button>
                                    <label for="ipset_import"><#WRIPSetImport#></label>
                                    <input type="file" id="ipset_import" accept=".json,application/json">
                                    <button type="button" id="ipset_export" class="btn"><#WRIPSetExport#></button>
                                    <p id="ipset_file_status" role="status"></p></td></tr>
                            <tr><th><label for="ipset_post"><#WRIPSetPostScript#></label></th>
                                <td><textarea id="ipset_post" class="span12" rows="5" maxlength="8192" spellcheck="false" name="scripts.wr-classic-ipset.post.sh"><% nvram_dump("scripts.wr-classic-ipset.post.sh",""); %></textarea></td></tr>
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
