"""Small, fail-closed transformation for the inherited VPN client badge."""
import re


def replace_legacy_wireguard_badge(page: str) -> str:
    """Stop vpnc_state from rendering a green WG/AWG Connected badge.

    The inherited state is controller/configuration state, not peer handshake
    or route evidence. The dedicated read-only interface/handshake observer
    owns the WG/AWG status display.
    """
    start = page.find("function update_vpnc_status(vpnc_state){")
    end = page.find("\nfunction applyRule()", start)
    if start < 0 or end < 0:
        raise ValueError("VPN status function anchors changed; no file written")
    before, function, after = page[:start], page[start:end], page[end:]
    pattern = re.compile(
        r"if \(vpnc_type == 3\) \{\s*"
        r"showhide_div\('col_vpnc_wg_state',[^\n]*\n"
        r".*?\n\t\} else \{",
        re.DOTALL,
    )
    replacement = (
        "if (vpnc_type == 3) {\n"
        "\t\t/* vpnc_state is not peer-handshake or route evidence. */\n"
        "\t\tshowhide_div('col_vpnc_wg_state', 0);\n"
        "\t} else {"
    )
    updated, count = pattern.subn(replacement, function, count=1)
    if count != 1 or "col_vpnc_wg_state" not in updated:
        raise ValueError("WireGuard legacy status branch changed; no file written")
    if "vpnc_state == 1" in updated or "vpnc_state == 2" in updated:
        raise ValueError("Legacy state still drives the WireGuard badge")
    return before + updated + after
