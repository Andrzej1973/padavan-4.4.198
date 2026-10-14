#!/usr/bin/env python3
"""Group Moon, static routes and the legacy NAT switch into one collapsed
advanced section and give the Moon network ID header a translation key.

Runs after localize-ui-page.py: the page already carries <#ZT_...#> keys.
The single Apply control is moved out of the routes table so it stays
reachable while the advanced section is collapsed. The section is collapsed by
page script only; without scripting every control stays visible, so no setting
becomes unreachable.

This changes source only. Device runtime behaviour is not verified here.
"""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
parser.add_argument('--verify-image', action='store_true')
args = parser.parse_args()

PAGE = 'trunk/user/www/n56u_ribbon_fixed/Advanced_zerotier.asp'
IMAGE_PAGE = 'trunk/romfs/www/Advanced_zerotier.asp'
ROW_CLASS = 'class="zt_advanced"'
TABLE_CLASS = 'class="table zt_advanced"'
TOGGLE_ID = 'zerotier_advanced_toggle'

NAT_ROW = '<tr> <th width="30%" style="border-top: 0 none;"><#ZT_AllowNAT#></th>'
NAT_ROW_GROUPED = '<tr class="zt_advanced"> <th width="30%" style="border-top: 0 none;"><#ZT_AllowNAT#></th>'
MOON_NETWORK_ROW = '<tr> <th>ZeroTier Moon Network ID</th>'
MOON_NETWORK_ROW_GROUPED = '<tr class="zt_advanced"> <th><#ZT_MoonNetworkID#></th>'
MOON_ENABLE_ROW = '<tr> <th width="30%" style="border-top: 0 none;"><#ZT_MoonEnable#></th>'
MOON_ENABLE_ROW_GROUPED = '<tr class="zt_advanced"> <th width="30%" style="border-top: 0 none;"><#ZT_MoonEnable#></th>'
MOON_ENDPOINT_ROW = '<tr> <th><#ZT_MoonEndpoint#></th>'
MOON_ENDPOINT_ROW_GROUPED = '<tr class="zt_advanced"> <th><#ZT_MoonEndpoint#></th>'
MOON_ID_ROW = '<tr> <th><#ZT_MoonID#></th>'
MOON_ID_ROW_GROUPED = '<tr class="zt_advanced"> <th><#ZT_MoonID#></th>'

TAB = '\t'
ROUTES_TABLE_OPEN = (TAB * 9 + '<table width="100%" align="center" cellpadding="4" cellspacing="0" class="table">\n'
                     + TAB * 10 + '<tr> <th colspan="4"><#ZT_RoutesHelp#></th> </tr>\n')
ROUTES_TABLE_OPEN_GROUPED = (TAB * 9 + '<table width="100%" align="center" cellpadding="4" cellspacing="0" class="table zt_advanced">\n'
                             + TAB * 10 + '<tr> <th colspan="4"><#ZT_RoutesHelp#></th> </tr>\n')
ROUTES_TABLE_CLOSE = TAB * 9 + '</table>\n' + TAB * 8 + '</div>\n'

APPLY_ROW = (TAB * 10 + '<tr>\n'
             + TAB * 11 + '<td colspan="4" style="border-top: 0 none;">\n'
             + TAB * 12 + '<br />\n'
             + TAB * 12 + '<center><input class="btn btn-primary" style="width: 219px" type="button" value="<#CTL_apply#>" onclick="applyRule()" /></center>\n'
             + TAB * 11 + '</td>\n'
             + TAB * 10 + '</tr>\n')
APPLY_AREA = (TAB * 9 + '<div style="text-align: center; padding: 10px 0;">\n'
              + TAB * 10 + '<input class="btn btn-primary" style="width: 219px" type="button" value="<#CTL_apply#>" onclick="applyRule()" />\n'
              + TAB * 9 + '</div>\n')

TOGGLE_ROW = (TAB * 10 + '<tr>\n'
              + TAB * 11 + '<th width="30%" style="border-top: 0 none;"><#ZT_AdvancedHeading#></th>\n'
              + TAB * 11 + '<td colspan="3" style="border-top: 0 none;">\n'
              + TAB * 12 + '<input type="button" id="zerotier_advanced_toggle" class="btn" value="<#ZT_AdvancedShow#>" onclick="wrZerotierAdvancedToggle();" />\n'
              + TAB * 12 + '<p><#ZT_AdvancedHelp#></p>\n'
              + TAB * 11 + '</td>\n'
              + TAB * 10 + '</tr>\n')

ADVANCED_JS = '''function wrZerotierAdvancedNodes() {
	return document.querySelectorAll('.zt_advanced');
}
function wrZerotierAdvancedSet(show) {
	var nodes = wrZerotierAdvancedNodes();
	for (var i = 0; i < nodes.length; i++) {
		nodes[i].style.display = show ? (nodes[i].tagName === 'TR' ? 'table-row' : 'table') : 'none';
	}
	var button = document.getElementById('zerotier_advanced_toggle');
	if (button) button.value = show ? '<#ZT_AdvancedHide#>' : '<#ZT_AdvancedShow#>';
}
function wrZerotierAdvancedToggle() {
	var nodes = wrZerotierAdvancedNodes();
	wrZerotierAdvancedSet(nodes.length > 0 && nodes[0].style.display === 'none');
}
function wrZerotierAdvancedInit() {
	wrZerotierAdvancedSet(false);
}
'''

INIT_ANCHOR = '\twrZerotierStartAutoRefresh();'
INIT_REPLACEMENT = INIT_ANCHOR + '\n\twrZerotierAdvancedInit();'


def replace_once(text, old, new, what):
    count = text.count(old)
    if count != 1:
        raise SystemExit('ZeroTier advanced %s anchor mismatch (%d matches): %r'
                         % (what, count, old[:70]))
    return text.replace(old, new)


if args.verify_image:
    page = (args.source / IMAGE_PAGE).read_text(encoding='utf-8')
    if page.count(ROW_CLASS) != 5 or page.count(TABLE_CLASS) != 1:
        raise SystemExit('Advanced ZeroTier group is incomplete in the image')
    for marker in (TOGGLE_ID, 'wrZerotierAdvancedToggle', 'wrZerotierAdvancedInit',
                   '<#ZT_MoonNetworkID#>'):
        if marker not in page:
            raise SystemExit('Missing ZeroTier advanced control: ' + marker)
    if 'ZeroTier Moon Network ID' in page:
        raise SystemExit('ZeroTier Moon header is not localized')
    if '<center><input class="btn btn-primary"' in page:
        raise SystemExit('Apply control is still inside the advanced group')
    if page.count('<#CTL_apply#>') != 1:
        raise SystemExit('Expected exactly one reachable Apply control')
    if page.count('function wrZerotierAdvancedToggle()') != 1:
        raise SystemExit('Advanced group script is missing or duplicated')
    print('PASS ZeroTier advanced group, Moon header key and reachable Apply control')
    raise SystemExit(0)

page_path = args.source / PAGE
page = page_path.read_text(encoding='utf-8')
page = replace_once(page, NAT_ROW, NAT_ROW_GROUPED, 'legacy NAT row')
page = replace_once(page, MOON_NETWORK_ROW, MOON_NETWORK_ROW_GROUPED, 'Moon network ID header')
page = replace_once(page, MOON_ENABLE_ROW, MOON_ENABLE_ROW_GROUPED, 'Moon enable row')
page = replace_once(page, MOON_ENDPOINT_ROW, MOON_ENDPOINT_ROW_GROUPED, 'Moon endpoint row')
page = replace_once(page, MOON_ID_ROW, MOON_ID_ROW_GROUPED, 'Moon ID row')
page = replace_once(page, ROUTES_TABLE_OPEN, ROUTES_TABLE_OPEN_GROUPED, 'routes table')
page = replace_once(page, APPLY_ROW, '', 'Apply row removal')
page = replace_once(page, ROUTES_TABLE_CLOSE, ROUTES_TABLE_CLOSE + APPLY_AREA, 'Apply placement')
page = replace_once(page, NAT_ROW_GROUPED, TOGGLE_ROW + NAT_ROW_GROUPED, 'advanced toggle row')
page = replace_once(page, 'function initial(){', ADVANCED_JS + 'function initial(){', 'advanced script')
page = replace_once(page, INIT_ANCHOR, INIT_REPLACEMENT, 'advanced initialisation')
if page.count(ROW_CLASS) != 5 or page.count(TABLE_CLASS) != 1:
    raise SystemExit('Advanced ZeroTier grouping did not apply as expected')
with page_path.open('w', encoding='utf-8', newline='\n') as stream:
    stream.write(page)
print('Grouped ZeroTier Moon, routes and legacy NAT under one collapsed advanced section; runtime unverified')
