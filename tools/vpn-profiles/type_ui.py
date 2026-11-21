"""Helpers for removing protocols unavailable in the WR1200JS profile."""
import re


_UNAVAILABLE_LEGACY_TYPES = (
    ("0", "PPTP"),
    ("1", "L2TP (w/o IPSec)"),
)


def remove_unavailable_legacy_types(page, field, allow_missing=False):
    """Remove unavailable PPTP/L2TP options, optionally accepting prior removal."""
    for value, label in _UNAVAILABLE_LEGACY_TYPES:
        option = (f'<option value="{value}" <% nvram_match_x("", "{field}", '
                  f'"{value}","selected"); %>>{label}</option>')
        pattern = re.compile(r'(?m)^[ \t]*' + re.escape(option) + r'\r?\n')
        page, count = pattern.subn("", page)
        if count != 1 and not (allow_missing and count == 0):
            raise RuntimeError(
                f"expected one unavailable {label} option for {field}; found {count}"
            )
    return page


def remove_unavailable_vpn_types(page, field, allow_legacy_missing=False):
    """Remove PPTP/L2TP and OpenVPN, preserving the supported WG selector."""
    page = remove_unavailable_legacy_types(
        page, field, allow_missing=allow_legacy_missing)
    pattern = re.compile(
        r'(?m)^[ \t]*<option value="2"[^>]*>.*?</option>\r?\n')
    page, count = pattern.subn("", page)
    if count != 1:
        raise RuntimeError(
            f"expected one unavailable OpenVPN option for {field}; found {count}"
        )
    return page


def require_openvpn_capability_hook(page, field):
    """Keep the inherited value-based gate, or upgrade one legacy index gate."""
    value_hook = f'$j("#{field} option[value=\'2\']").remove();'
    index_hook = f'document.form.{field}.remove(2);'
    if page.count(value_hook) == 1 and page.count(index_hook) == 0:
        return page
    if page.count(index_hook) == 1 and page.count(value_hook) == 0:
        return page.replace(index_hook, value_hook, 1)
    raise RuntimeError(f"OpenVPN capability hook changed: {field}")
