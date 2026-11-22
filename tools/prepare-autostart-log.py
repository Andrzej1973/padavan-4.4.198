#!/usr/bin/env python3
"""Translate inherited autostart log messages without changing startup logic."""
import argparse
from pathlib import Path

MESSAGES = {
    "防止 DNSmasq 启动失败，创建/tmp/dnsmasq.dom/": "dnsmasq startup: ensured /tmp/dnsmasq.dom exists",
    "自动启动": "Autostart",
    "正在检查路由是否已连接互联网...": "Checking router Internet connectivity...",
    "正在启动 SQM QOS...": "Starting SQM QoS...",
    "正在启动 Adbyby plus...": "Starting Adbyby Plus...",
    "正在启动 adguardhome...": "Starting AdGuard Home...",
    "正在启动科学上网...": "Starting Shadowsocks...",
    "正在启动 SmartDNS...": "Starting SmartDNS...",
    "正在启动阿里ddns...": "Starting AliDDNS...",
    "正在启动 ddnsto...": "Starting DDNSTO...",
    "正在启动阿里云盘...": "Starting Aliyun Drive WebDAV...",
    "正在启动 zerotier...": "Starting ZeroTier...",
    "正在启动 wireguard...": "Starting WireGuard...",
    "正在启动frp client...": "Starting FRP client...",
}


def translate(text: str) -> str:
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if line.lstrip().startswith("logger "):
            for source, translation in MESSAGES.items():
                line = line.replace(f'"{source}"', f'"{translation}"')
            if any("\u4e00" <= char <= "\u9fff" for char in line):
                raise ValueError(f"Untranslated autostart logger line {index + 1}")
            lines[index] = line
    result = "".join(lines)
    if 'logger -t "Autostart" "Checking router Internet connectivity..."' not in result:
        raise ValueError("Connectivity log anchor missing from autostart script")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("script", type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    source = args.script.read_bytes()
    translated = translate(source.decode("utf-8")).encode("utf-8")
    if args.check:
        if translated != source:
            parser.error("Autostart log messages still require translation")
    elif translated != source:
        args.script.write_bytes(translated)
