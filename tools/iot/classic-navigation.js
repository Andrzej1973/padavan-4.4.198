/* Classic navigation only. This asset never reads or writes router settings. */
(function () {
    'use strict';
    var pairs = [
        ['Advanced_Wireless2g_Content.asp', 'Advanced_Wireless_Content.asp'],
        ['Advanced_WGuest2g_Content.asp', 'Advanced_WGuest_Content.asp'],
        ['Advanced_WMode2g_Content.asp', 'Advanced_WMode_Content.asp'],
        ['Advanced_ACL2g_Content.asp', 'Advanced_ACL_Content.asp'],
        ['Advanced_WSecurity2g_Content.asp', 'Advanced_WSecurity_Content.asp'],
        ['Advanced_WAdvanced2g_Content.asp', 'Advanced_WAdvanced_Content.asp']
    ];
    function item(list, label, href, active) {
        var li = document.createElement('li'), a = document.createElement('a');
        a.appendChild(document.createTextNode(label));
        a.setAttribute('href', href);
        if (active) {
            li.className = 'active';
            a.setAttribute('aria-current', 'page');
        }
        li.appendChild(a); list.appendChild(li);
    }
    function mount() {
        var path = window.location.pathname.split('/').pop(), pair = null, i;
        var tab = document.getElementById('tabMenu'), list, isIot;
        if (document.getElementById('wr-classic-radio-tabs')) return;
        isIot = path === 'Advanced_IoT_Content.asp';
        for (i = 0; i < pairs.length; i++) {
            if (pairs[i][0] === path || pairs[i][1] === path) pair = pairs[i];
        }
        if (tab && (pair || isIot)) {
            pair = pair || pairs[0];
            list = document.createElement('ul');
            list.id = 'wr-classic-radio-tabs';
            list.className = 'nav nav-tabs';
            list.setAttribute('aria-label', 'Wi-Fi');
            item(list, '2.4GHz', '/' + pair[0], path === pair[0]);
            item(list, '5GHz', '/' + pair[1], path === pair[1]);
            item(list, 'IoT', '/Advanced_IoT_Content.asp', isIot);
            tab.parentNode.insertBefore(list, tab);
        }
        /* Shared Classic banner: retain the original two buttons and classes. */
        var band5 = document.getElementById('wifi5_b');
        if (band5 && !document.getElementById('wifi_iot_b')) {
            var link = document.createElement('a');
            link.id = 'wifi_iot_b'; link.className = 'btn btn-mini' + (isIot ? ' btn-info' : '');
            link.setAttribute('href', '/Advanced_IoT_Content.asp');
            link.appendChild(document.createTextNode('IoT'));
            if (isIot) link.setAttribute('aria-current', 'page');
            band5.parentNode.appendChild(document.createTextNode(' '));
            band5.parentNode.appendChild(link);
        }
        var sidebar = document.getElementById('subMenu');
        if (sidebar && !document.getElementById('wr-classic-iot-menu')) {
            var menuLink = document.createElement('a'), icon = document.createElement('i');
            menuLink.id = 'wr-classic-iot-menu';
            menuLink.setAttribute('href', '/Advanced_IoT_Content.asp');
            icon.className = 'icon-minus'; menuLink.appendChild(icon);
            menuLink.appendChild(document.createTextNode('  IoT'));
            if (isIot) {
                menuLink.className = 'active';
                menuLink.setAttribute('aria-current', 'page');
            }
            sidebar.appendChild(menuLink);
        }
    }
    if (document.readyState === 'complete') mount();
    else window.addEventListener('load', mount, false);
}());
