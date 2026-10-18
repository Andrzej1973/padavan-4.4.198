#!/usr/bin/env python3
"""Validate that generated setup manuals retain required service guidance."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=Path)
    parser.add_argument("text", type=Path)
    args = parser.parse_args()
    markdown = args.markdown.read_text(encoding="utf-8")
    text = args.text.read_text(encoding="utf-8")
    for value in (markdown, text):
        if "ZeroTier" not in value or "Stubby" not in value:
            raise SystemExit("guide lacks enabled ZeroTier or Stubby chapter")
        if "Не публікуйте" not in value:
            raise SystemExit("guide lacks credential-safety instruction")
        if "Заміна порту WAN" not in value or "switch 67" not in value:
            raise SystemExit("guide lacks the WAN socket replacement guidance")
        if "Параметр профілю: CONFIG_FIRMWARE_INCLUDE_SSLOCAL=y" in value:
            for required in ("ss-local", "SOCKS5", "ss-server", "CONFIG_FIRMWARE_INCLUDE_SSSERVER"):
                if required not in value:
                    raise SystemExit("Shadowsocks guide lacks client/server distinction: " + required)
        if "CONFIG_FIRMWARE_INCLUDE_DOH=y" in value:
            for required in ("Слоти DoH 1–4", "повторний PID", "/var/run/doh-proxy/0.log", "не перевірка порту", "ручним редагуванням PID-файлів"):
                if required not in value:
                    raise SystemExit("DoH guide lacks instance diagnostic guidance: " + required)
        if "Параметр профілю: CONFIG_FIRMWARE_INCLUDE_WIREGUARD=y" in value:
            for required in ("Зберегти новий профіль", "ID спільні", "16 КіБ",
                             "Збереження не запускає тунель", "спершу оновіть список",
                             "/etc/storage/wrvpn", "чинний тунель доступу",
                             "Редагувати профіль", "Застаріла ревізія", "Скасувати й очистити"):
                if required not in value:
                    raise SystemExit("VPN guide lacks independent create guidance: " + required)
    if "https://central.zerotier.com/" not in markdown:
        raise SystemExit("markdown guide lacks official ZeroTier Central link")
    if "dnsprivacy.org" not in markdown:
        raise SystemExit("markdown guide lacks official Stubby link")
    for content in (markdown, text):
        for required in ("свіжий кеш спостережень", "4096 байтами", "раз на 30 секунд"):
            if required not in content:
                raise SystemExit("guide lacks ZeroTier status usage: " + required)
    print("router guide checks passed")


if __name__ == "__main__":
    main()
