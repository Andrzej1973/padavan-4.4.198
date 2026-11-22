#!/usr/bin/env python3
"""Keep the authenticated Classic reboot control and remove the power-off button."""
import argparse
import re
from pathlib import Path

REBOOT = """function reboot(){
	if(!confirm('<#JS_reboot#>'))
		return;
	var $j = jQuery.noConflict();
	$j.post('/apply.cgi', {'action_mode': ' Reboot ', 'current_page': 'index.asp'})
		.done(function(){ showLoading(board_boot_time()); })
		.fail(function(xhr){
			if (xhr.status) alert('HTTP ' + xhr.status + ': ' + xhr.statusText);
		});
}
"""

def transform(state):
    if REBOOT in state and 'id="shutdown_btn"' not in state:
        return state
    state, removed = re.subn(r' <button type="button" id="shutdown_btn"[^>]*>.*?</button>', '', state)
    state, replaced = re.subn(r'^function reboot\(\)\s*\{.*?^\}\n', lambda _: REBOOT, state,
                              flags=re.MULTILINE | re.DOTALL)
    if removed != 1 or replaced != 1 or 'id="reboto_btn"' not in state:
        raise ValueError("Classic power control anchors changed")
    return state


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    path = args.source / "trunk/user/www/n56u_ribbon_fixed/state.js"
    path.write_text(transform(path.read_text(encoding="utf-8")), encoding="utf-8", newline="\n")
