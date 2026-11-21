(function (root) {
    'use strict';
    var token = '', revision = '', busy = false, generation = 0, expires = 0, capturedAt = 0;
    var runtimeProfile = null;
    function element(id) { return root.document.getElementById(id); }
    function message(text) { element('iot-message').textContent = text; }
    function lock(value) {
        busy = value;
        ['iot-refresh', 'iot-ram', 'iot-auto', 'iot-save'].forEach(function (id) {
            element(id).disabled = value || (id !== 'iot-refresh' && !revision);
        });
        ['iot-on','iot-off'].forEach(function (id) { element(id).disabled = value || !revision || !runtimeProfile; });
    }
    function request(url, data, done) {
        root.jQuery.ajax({url: url, type: 'POST', data: data, dataType: 'json', timeout: 4000,
            success: function (reply) { done(null, reply); },
            error: function () { done(new Error('request_failed')); }});
    }
    function refresh() {
        if (busy) { return; }
        revision = ''; expires = 0; runtimeProfile = null; lock(true); message('Читання налаштувань…');
        root.jQuery.ajax({url: '/wr_iot_token.cgi', dataType: 'json', cache: false, timeout: 4000,
            success: function (reply) {
                if (!reply || !/^[0-9a-f]{32}$/.test(reply.token)) { finish(); return; }
                token = reply.token;
                request('/wr_iot_view.cgi', {token: token}, function (error, view) {
                    if (error || !view || !/^[0-9a-f]{32}$/.test(view.revision) ||
                        typeof view.configured !== 'boolean' || typeof view.enabled !== 'boolean' ||
                        typeof view.key_present !== 'boolean' || view.configured !== view.key_present ||
                        ['ssid', 'gateway', 'mask', 'first', 'last'].some(function (key) {
                            return typeof view[key] !== 'string' || view[key].length > (key === 'ssid' ? 32 : 15);
                        }) || (!view.configured && (view.enabled || ['ssid', 'gateway', 'mask', 'first', 'last'].some(function (key) { return view[key] !== ''; })))) {
                        finish(); return;
                    }
                    revision = view.revision;
                    capturedAt = Date.now(); expires = capturedAt + 110000;
                    if (view.configured) {
                        runtimeProfile = {};
                        ['ssid','gateway','mask','first','last'].forEach(function (key) { runtimeProfile[key] = view[key]; });
                    }
                    element('iot-enabled').checked = view.enabled;
                    ['ssid', 'gateway', 'mask', 'first', 'last'].forEach(function (key) { element('iot-' + key).value = view[key]; });
                    element('iot-action').value = view.key_present ? 'keep' : 'replace';
                    element('iot-password').value = '';
                    updateKey(); lock(false);
                    message('Прочитано бажані налаштування. Це не підтвердження роботи Wi-Fi.');
                });
            }, error: finish});
        function finish() { lock(false); message('Налаштування недоступні. Повторіть читання.'); }
    }
    function updateKey() {
        var keep = element('iot-action').value === 'keep';
        element('iot-password').disabled = keep;
        if (keep) { element('iot-password').value = ''; }
    }
    function poll(id, serial, attempts, mode) {
        root.jQuery.ajax({url: '/wr_iot_result.cgi', data: {id: id}, dataType: 'json', cache: false, timeout: 4000,
            success: function (reply) {
                if (serial !== generation) { return; }
                if (!reply || reply.id !== id) { uncertain(); return; }
                if ((mode === 'runtime' && reply.state === 'applied') ||
                    (mode !== 'runtime' && (reply.state === 'stored_in_ram' || reply.state === 'saved_in_flash')) || reply.state === 'rejected') {
                    lock(false);
                    message(reply.state === 'applied' ? 'Запит перемикання виконано.' : reply.state === 'saved_in_flash' ? 'Збережено у flash. Мережу не активовано цією дією.' :
                        reply.state === 'stored_in_ram' ? 'Збережено в RAM. Після перезавантаження ці зміни можуть зникнути.' :
                        'Запит відхилено. Прочитайте актуальні налаштування.');
                } else if ((reply.state === 'queued' || reply.state === 'running') && attempts < 30) {
                    root.setTimeout(function () { poll(id, serial, attempts + 1, mode); }, 500);
                } else { uncertain(); }
            }, error: uncertain});
        function uncertain() {
            if (serial !== generation) { return; }
            lock(false); message('Результат невідомий або потрібне відновлення. Запис автоматично не повторюється.');
        }
    }
    function submit(mode, enabled) {
        if (busy || !revision) { return; }
        if (Date.now() < capturedAt || Date.now() >= expires) {
            revision = ''; lock(false); message('Строк редагування минув. Прочитайте налаштування ще раз.'); return;
        }
        var paths = {ram: '/wr_iot_edit_ram.cgi', auto: '/wr_iot_edit_auto.cgi', save: '/wr_iot_edit_save.cgi', runtime: '/wr_iot_edit_runtime.cgi'};
        if (!paths[mode]) { return; }
        if (mode === 'runtime' && (!runtimeProfile || (enabled !== 0 && enabled !== 1))) { return; }
        var data = {token: token, revision: revision, key_action: element('iot-action').value,
            wr_iot_request_enable: element('iot-enabled').checked ? '1' : '0',
            wr_iot_request_ssid: element('iot-ssid').value,
            wr_iot_request_psk: element('iot-action').value === 'keep' ? '' : element('iot-password').value,
            wr_iot_request_gateway: element('iot-gateway').value, wr_iot_request_mask: element('iot-mask').value,
            wr_iot_request_start: element('iot-first').value, wr_iot_request_end: element('iot-last').value};
        if (mode === 'runtime') {
            data.key_action = 'keep'; data.wr_iot_request_psk = ''; data.wr_iot_request_enable = String(enabled);
            data.wr_iot_request_ssid = runtimeProfile.ssid; data.wr_iot_request_gateway = runtimeProfile.gateway;
            data.wr_iot_request_mask = runtimeProfile.mask; data.wr_iot_request_start = runtimeProfile.first;
            data.wr_iot_request_end = runtimeProfile.last;
        }
        revision = ''; generation++; var serial = generation;
        lock(true); message('Передавання запиту…');
        request(paths[mode], data, function (error, reply) {
            data.wr_iot_request_psk = ''; element('iot-password').value = '';
            if (error || !reply || reply.accepted !== true || !/^[0-9a-f]{32}$/.test(reply.id)) {
                lock(false); message('Прийняття запиту не підтверджено. Автоматичного повтору немає.'); return;
            }
            message('Запит у черзі. Очікування результату…'); poll(reply.id, serial, 0, mode);
        });
    }
    root.wrIotConfig = {init: function () {
        element('iot-refresh').onclick = refresh;
        element('iot-action').onchange = updateKey;
        ['ram', 'auto', 'save'].forEach(function (mode) { element('iot-' + mode).onclick = function () { submit(mode); }; });
        element('iot-on').onclick = function () { submit('runtime', 1); };
        element('iot-off').onclick = function () { submit('runtime', 0); };
        lock(false); updateKey();
    }};
}(window));
