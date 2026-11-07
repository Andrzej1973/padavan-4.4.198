#!/usr/bin/env python3
"""Exercise the actual Stubby and DoH dnsmasq emitters together and alone."""
from pathlib import Path
import subprocess
import tempfile

import argparse
import os
import secrets


ROOT = Path(__file__).resolve().parents[1]
STUBBY = ROOT / "overlay/padavan-4.4/ports/stubby"
DOH = ROOT / "overlay/padavan-4.4/ports/doh"

HARNESS = r'''#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int stubby_enabled = 1, stubby_mode = 1, stubby_port = 5453;
static int stubby_listen_mode = 0;
static int doh_enabled = 1, doh_mode = 1, doh_port = 5053;
static int doh_listen_mode = 0;
static const char *lookup(const char *key)
{
    static char stubby_port_text[16];
    if (!strcmp(key, "stubby_enable")) return stubby_enabled ? "1" : "0";
    if (!strcmp(key, "stubby_mode")) return stubby_mode == 0 ? "0" : (stubby_mode == 3 ? "3" : "1");
    if (!strcmp(key, "stubby_listen_port")) {
        snprintf(stubby_port_text, sizeof(stubby_port_text), "%d", stubby_port);
        return stubby_port_text;
    }
    if (!strcmp(key, "stubby_listen_mode")) return stubby_listen_mode ? "1" : "0";
    if (!strcmp(key, "doh_enable")) return doh_enabled ? "1" : "0";
    if (!strcmp(key, "doh_mode")) return doh_mode ? "1" : "0";
    if (!strcmp(key, "doh_listen_port")) return doh_port == 5053 ? "5053" : "5453";
    if (!strcmp(key, "doh_listen_mode")) return doh_listen_mode ? "1" : "0";
    if (!strcmp(key, "doh_server0")) return "https://dns.google/dns-query";
    if (!strcmp(key, "doh_server1")) return "https://cloudflare-dns.com/dns-query";
    if (!strcmp(key, "doh_server2") || !strcmp(key, "doh_server3")) return "";
    if (!strcmp(key, "ntp_server0")) return "pool.ntp.org";
    if (!strcmp(key, "ntp_server1")) return "time.google.com";
    if (!strcmp(key, "lan_ipaddr_t")) return "192.168.1.1";
    return "";
}
int nvram_get_int(const char *key) { return atoi(lookup(key)); }
int nvram_match(const char *key, const char *value) { return !strcmp(lookup(key), value); }
const char *nvram_safe_get(const char *key) { return lookup(key); }
int is_valid_ipv4(const char *text)
{
    int parts = 0, digits = 0, value = 0;
    if (!text || !*text) return 0;
    for (; *text; text++) {
        if (*text >= '0' && *text <= '9') {
            if (++digits > 3) return 0;
            value = value * 10 + *text - '0';
            if (value > 255) return 0;
        } else if (*text == '.' && digits) {
            if (++parts > 3) return 0;
            digits = value = 0;
        } else return 0;
    }
    return parts == 3 && digits > 0;
}
int get_wan_dns_static(void) { return 0; }
const char *get_wan_unit_value(int unit, const char *key)
{
    static char value[32];
    (void)unit;
    (void)key;
    strcpy(value, "192.0.2.53");
    return value;
}
#define foreach(word, value, next) \
    for ((next) = (char *)(value), (word) = strsep(&(next), " \t"); \
         (word) != NULL; (word) = strsep(&(next), " \t"))

#define strsep(remaining, delimiters) next_word(remaining)
static char *next_word(char **remaining)
{
    char *word, *cursor;
    if (!remaining || !*remaining || !**remaining) return NULL;
    word = *remaining;
    for (cursor = word; *cursor && *cursor != ' ' && *cursor != '\t'; cursor++) { }
    if (*cursor) { *cursor++ = '\0'; *remaining = cursor; }
    else *remaining = NULL;
    return word;
}

void logmessage(const char *tag, const char *message)
{
    (void)tag;
    (void)message;
}
static void copy_next_word(char destination[256], char **remaining)
{
    char *word = next_word(remaining);
    if (word) snprintf(destination, 256, "%s", word);
    else destination[0] = '\0';
}
#undef foreach
#define foreach(word, value, next) \
    for ((next) = (char *)(value), copy_next_word((word), &(next)); \
         (word)[0]; copy_next_word((word), &(next)))

#include "dnsmasq-stubby.c"
#include "dnsmasq-doh.c"

static char *render(void)
{
    char *text;
    long length;
    FILE *fp = tmpfile();
    if (!fp) return NULL;
    stubby_dnsmasq_config(fp);
    doh_dnsmasq_config(fp);
    if (fflush(fp) || fseek(fp, 0, SEEK_END) || (length = ftell(fp)) < 0 ||
        fseek(fp, 0, SEEK_SET)) { fclose(fp); return NULL; }
    text = malloc((size_t)length + 1);
    if (!text) { fclose(fp); return NULL; }
    {
        size_t read_length = fread(text, 1, (size_t)length, fp);
        int close_status = fclose(fp);
        if (read_length != (size_t)length || close_status) {
            free(text);
            return NULL;
        }
    }
    text[length] = '\0';
    return text;
}
static int count_line(const char *text, const char *line)
{
    const char *start = text;
    int count = 0;
    size_t length = strlen(line);
    while ((text = strstr(text, line)) != NULL) {
        if ((text == start || text[-1] == '\n') && text[length] == '\n') count++;
        text += length;
    }
    return count;
}
static int has(const char *text, const char *line) { return count_line(text, line) == 1; }
static int check(const char *name, const char *text, int expected_resolv,
                 int expected_stubby, int expected_doh)
{
    int resolv = count_line(text, "no-resolv");
    int stubby = count_line(text, "server=127.0.0.1#5453");
    int doh = count_line(text, "server=127.0.0.1#5053") +
              count_line(text, "server=127.0.0.1#5054") +
              count_line(text, "server=127.0.0.1#5055") +
              count_line(text, "server=127.0.0.1#5056");
    int ok = resolv == expected_resolv && stubby == expected_stubby && doh == expected_doh;
    if (count_line(text, "server=/pool.ntp.org/192.0.2.53") != expected_resolv) ok = 0;
    if (count_line(text, "server=/time.google.com/192.0.2.53") != expected_resolv) ok = 0;
    if (expected_stubby && !has(text, "server=127.0.0.1#5453")) ok = 0;
    if (expected_doh && (!has(text, "server=127.0.0.1#5053") ||
                         !has(text, "server=127.0.0.1#5054"))) ok = 0;
    if (expected_resolv == 0 && strstr(text, "server=/")) ok = 0;
    printf("%s %s (no-resolv=%d, Stubby=%d, DoH=%d)\n",
           ok ? "PASS" : "FAIL", name, resolv, stubby, doh);
    return ok;
}
int main(int argc, char **argv)
{
    int ok = 1;
    char *text;
    if (argc == 2 && !strcmp(argv[1], "--config-only")) {
        text = render();
        if (!text) return 2;
        fputs("port=0\n", stdout);
        fputs(text, stdout);
        free(text);
        return ferror(stdout) ? 2 : 0;
    }
    text = render();
    if (!text) return 2;
    ok &= check("both encrypted DNS modes contribute valid upstreams", text, 2, 1, 2);
    free(text);
    doh_enabled = 0;
    text = render();
    if (!text) return 2;
    ok &= check("Stubby-only router DNS", text, 1, 1, 0);
    free(text);
    stubby_enabled = 0;
    doh_enabled = 1;
    text = render();
    if (!text) return 2;
    ok &= check("DoH-only router DNS", text, 1, 0, 2);
    free(text);
    stubby_enabled = 1;
    stubby_mode = 0;
    text = render();
    if (!text) return 2;
    ok &= check("standalone Stubby does not add a dnsmasq upstream", text, 1, 0, 2);
    free(text);
    doh_enabled = 0;
    stubby_mode = 1;
    {
        const int ports[] = {0, 53, 1023, 1024, 65535, 65536};
        size_t i;
        for (i = 0; i < sizeof(ports) / sizeof(ports[0]); i++) {
            char line[64];
            int valid = ports[i] >= 1024 && ports[i] <= 65535;
            int accepted;
            stubby_port = ports[i];
            text = render();
            if (!text) return 2;
            snprintf(line, sizeof(line), "server=127.0.0.1#%d", ports[i]);
            accepted = has(text, line);
            if (accepted != valid || count_line(text, "no-resolv") != 1 ||
                (!valid && strstr(text, "server=127.0.0.1#"))) ok = 0;
            printf("%s Stubby port %d: upstream %s, no-resolv retained\n",
                   accepted == valid && count_line(text, "no-resolv") == 1 ? "PASS" : "FAIL",
                   ports[i], accepted ? "emitted" : "omitted");
            free(text);
        }
    }
    return ok ? 0 : 1;
}
'''


def make_qemu_test_root(destination, image_root, config):
    """Expose the image libraries and a host-seeded /dev/urandom to QEMU."""
    image_root = image_root.resolve(strict=True)
    destination.mkdir()

    def resolve_image_path(relative):
        path = image_root / relative
        seen = set()
        while path.is_symlink():
            marker = str(path)
            if marker in seen:
                raise RuntimeError(f"symlink cycle in target sysroot: {relative}")
            seen.add(marker)
            target = Path(os.readlink(path))
            if target.is_absolute():
                path = image_root / str(target).lstrip("/\\")
            else:
                path = path.parent / target
            path = Path(os.path.normpath(path))
            try:
                path.relative_to(image_root)
            except ValueError as error:
                raise RuntimeError(f"target sysroot link escapes image: {relative}") from error
        return path

    for entry in image_root.iterdir():
        if entry.name in {"dev", "tmp"}:
            continue
        source = resolve_image_path(entry.name)
        if source.exists():
            os.symlink(str(source), destination / entry.name,
                       target_is_directory=source.is_dir())

    dev = destination / "dev"
    dev.mkdir()
    image_dev = image_root / "dev"
    if image_dev.is_dir():
        for entry in image_dev.iterdir():
            if entry.name in {"urandom", "random", "null", "zero"}:
                continue
            source = resolve_image_path(Path("dev") / entry.name)
            if source.exists():
                os.symlink(str(source), dev / entry.name,
                           target_is_directory=source.is_dir())
    (dev / "null").symlink_to(os.devnull)
    (dev / "zero").symlink_to("/dev/zero")
    (dev / "random").symlink_to("/dev/urandom")
    # QEMU's image-root mapping can expose ROMFS /dev/urandom as an empty
    # placeholder. dnsmasq needs 176 bytes to seed SURF before parsing options.
    (dev / "urandom").write_bytes(secrets.token_bytes(4096))

    guest_tmp = destination / "tmp"
    guest_tmp.mkdir()
    guest_config = guest_tmp / config.name
    guest_config.write_bytes(config.read_bytes())
    return guest_config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tree", type=Path,
                        help="prepared Padavan source tree to verify integration markers")
    parser.add_argument("--dnsmasq", type=Path,
                        help="built target dnsmasq binary to parse the combined config")
    parser.add_argument("--qemu", default="",
                        help="optional qemu-user executable for the target binary")
    parser.add_argument("--sysroot", type=Path,
                        help="optional target root used by qemu-user (-L)")
    parser.add_argument("--cc", default="gcc" if os.name == "nt" else "cc",
                        help="native C compiler used to execute the emitter fixture")
    args = parser.parse_args()
    if args.tree:
        services = args.tree / "trunk/user/rc/services_ex.c"
        text = services.read_text(encoding="utf-8")
        for call in ("stubby_dnsmasq_config(fp);", "doh_dnsmasq_config(fp);"):
            if text.count(call) != 1:
                raise SystemExit(f"Expected exactly one final dnsmasq call: {call}")
        print("PASS final WR1200JS services_ex.c includes both DNS emitters once")
    with tempfile.TemporaryDirectory(prefix="encrypted-dnsmasq-check-", dir=ROOT) as temp:
        temp = Path(temp)
        source = temp / "check.c"
        binary = temp / ("check.exe" if os.name == "nt" else "check")
        source.write_text(HARNESS, encoding="utf-8")
        subprocess.run([
            args.cc, "-std=gnu99", "-Wall", "-Wextra", "-Werror", "-O2",
            "-I", str(STUBBY), "-I", str(DOH), str(source), "-o", str(binary),
        ], check=True)
        subprocess.run([str(binary)], check=True)
        if args.dnsmasq:
            config = temp / "combined-dnsmasq.conf"
            config.write_text(subprocess.run(
                [str(binary), "--config-only"], check=True, capture_output=True,
                text=True).stdout, encoding="utf-8")
            command = []
            if args.qemu:
                if not args.sysroot:
                    parser.error("--sysroot is required with --qemu")
                qemu_root = temp / "qemu-sysroot"
                guest_config = make_qemu_test_root(qemu_root, args.sysroot, config)
                command = [args.qemu, "-L", str(qemu_root)]
                config_arg = "/tmp/" + guest_config.name
            else:
                config_arg = str(config)
            command += [str(args.dnsmasq), "--test", "--conf-file=" + config_arg]
            subprocess.run(command, check=True)
            print("PASS built target dnsmasq accepts the combined DoT/DoH config")


if __name__ == "__main__":
    main()
