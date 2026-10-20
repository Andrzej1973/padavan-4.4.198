"""Helpers for removing protocols unavailable in the WR1200JS profile."""
import re


_UNAVAILABLE_LEGACY_TYPES = (
    ("0", "PPTP"),
    ("1", "L2TP (w/o IPSec)"),
)


def remove_unavailable_legacy_types(page, field):
    """Remove exactly one PPTP and L2TP option from a VPN type selector."""
    for value, label in _UNAVAILABLE_LEGACY_TYPES:
        option = (f'<option value="{value}" <% nvram_match_x("", "{field}", '
                  f'"{value}","selected"); %>>{label}</option>')
        pattern = re.compile(r'(?m)^[ \t]*' + re.escape(option) + r'\r?\n')
        page, count = pattern.subn("", page)
        if count != 1:
            raise RuntimeError(
                f"expected one unavailable {label} option for {field}; found {count}"
            )
    return page
