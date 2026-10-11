#!/usr/bin/env python3
"""Require an httpd route for every file the image serves from /www.

httpd answers 404 for any request matching no mime_handlers entry, even when
the file exists in ROMFS. Resolve the effective table from web_ex.c using the
APP_* macros cflags.mk derives from the firmware .config, then apply httpd's
own first-match ?/*/** matcher to each installed file.
"""
import argparse
import json
import os
import re
import sys
from pathlib import Path

# Read by httpd itself for translations; never requested by the browser.
INTERNAL = re.compile(r'(^|/)([A-Z]{2}\.dict|EN\.header)$')


def match_one(pattern, string):
    """Port of httpd.c match_one: ? one char, * no slash, ** anything."""
    p = 0
    s = 0
    while p < len(pattern):
        if pattern[p] == '?' and s < len(string):
            p += 1
            s += 1
            continue
        if pattern[p] == '*':
            p += 1
            if p < len(pattern) and pattern[p] == '*':
                p += 1
                limit = len(string) - s
            else:
                slash = string.find('/', s)
                limit = (slash if slash >= 0 else len(string)) - s
            return any(match_one(pattern[p:], string[s + i:]) for i in range(limit, -1, -1))
        if s >= len(string) or pattern[p] != string[s]:
            return False
        p += 1
        s += 1
    return s == len(string)


def match(pattern, string):
    return any(match_one(part, string) for part in pattern.split('|'))


def config_macros(cflags_text, config_text):
    """APP_* macros cflags.mk adds for options set to y in the .config."""
    enabled = set(re.findall(r'^(CONFIG_\w+)=y$', config_text, re.M))
    known = {}
    for option, macro in re.findall(
            r'^ifeq \(\$\((CONFIG_\w+)\),y\)\s*\nCFLAGS \+= -D(\w+)\s*$', cflags_text, re.M):
        known[macro] = option in enabled
    for option, macro in re.findall(
            r'^CFLAGS \+= \$\(if \$\((CONFIG_\w+)\),-D(\w+),\)\s*$', cflags_text, re.M):
        known[macro] = option in enabled
    return known


def evaluate(expression, defines, assumed):
    """Evaluate the defined()/!/&&/|| subset used around mime handlers."""
    def name_value(m):
        name = m.group(1)
        if name not in defines:
            assumed.add(name)
        return ' True ' if defines.get(name) else ' False '
    text = re.sub(r'defined\s*\(\s*(\w+)\s*\)', name_value, expression)
    text = re.sub(r'defined\s+(\w+)', name_value, text)
    text = text.replace('&&', ' and ').replace('||', ' or ')
    text = re.sub(r'!(?!=)', ' not ', text)
    if not re.fullmatch(r'[\s()]*((True|False|and|or|not)[\s()]*)+', text):
        raise SystemExit('Unsupported preprocessor condition in mime_handlers: ' + expression)
    return eval(text)  # Only True/False/and/or/not/() remain.


def effective_routes(web_ex_text, defines):
    start = web_ex_text.find('struct mime_handler mime_handlers[] = {')
    if start < 0 or web_ex_text.count('struct mime_handler mime_handlers[] = {') != 1:
        raise SystemExit('Expected exactly one mime_handlers table in web_ex.c')
    end = web_ex_text.find('\n};', start)
    if end < 0:
        raise SystemExit('Unterminated mime_handlers table')
    routes = []
    assumed = set()
    stack = []  # (active, any_branch_taken)
    for raw in web_ex_text[start:end].splitlines()[1:]:
        line = raw.strip()
        directive = re.match(r'#\s*(\w+)\s*(.*)', line)
        if directive:
            word, rest = directive.group(1), re.sub(r'/[/*].*', '', directive.group(2)).strip()
            if word == 'if':
                value = evaluate(rest, defines, assumed)
                stack.append((value, value))
            elif word in ('ifdef', 'ifndef'):
                value = evaluate('defined(%s)' % rest, defines, assumed)
                value = value if word == 'ifdef' else not value
                stack.append((value, value))
            elif word == 'elif':
                if not stack:
                    raise SystemExit('Unbalanced #elif in mime_handlers')
                taken = stack[-1][1]
                value = not taken and evaluate(rest, defines, assumed)
                stack[-1] = (value, taken or value)
            elif word == 'else':
                if not stack:
                    raise SystemExit('Unbalanced #else in mime_handlers')
                stack[-1] = (not stack[-1][1], True)
            elif word == 'endif':
                if not stack:
                    raise SystemExit('Unbalanced #endif in mime_handlers')
                stack.pop()
            else:
                raise SystemExit('Unsupported directive in mime_handlers: ' + line)
            continue
        if not all(active for active, _ in stack):
            continue
        entry = re.match(r'\{\s*"([^"]+)"\s*,\s*"([^"]*)"\s*,[^,]*,[^,]*,\s*(\w+)\s*,\s*(\d)\s*\}', line)
        if entry:
            routes.append({'pattern': entry.group(1), 'mime': entry.group(2),
                           'output': entry.group(3), 'auth': int(entry.group(4))})
    if stack:
        raise SystemExit('Unbalanced conditionals in mime_handlers')
    if not routes:
        raise SystemExit('No mime handlers resolved from web_ex.c')
    return routes, sorted(assumed)


def served_files(www):
    files = []
    for directory, dirs, names in os.walk(www):
        # The custom link points at /opt on the router and is empty in ROMFS.
        dirs[:] = [d for d in dirs if not os.path.islink(os.path.join(directory, d))]
        for name in names:
            # File links such as dlink.js resolve on the router and are served.
            relative = os.path.relpath(os.path.join(directory, name), www).replace(os.sep, '/')
            if not INTERNAL.search(relative):
                files.append(relative)
    return sorted(files)


def check(trunk, www, config, extra_defines):
    defines = config_macros((trunk / 'user/shared/cflags.mk').read_text(encoding='utf-8'),
                            config.read_text(encoding='utf-8'))
    defines.update({name: True for name in extra_defines})
    routes, assumed = effective_routes(
        (trunk / 'user/httpd/web_ex.c').read_text(encoding='utf-8', errors='replace'), defines)
    files = served_files(www)
    if not files:
        raise SystemExit('No served files found under ' + str(www))
    routed = {}
    unrouted = []
    for name in files:
        route = next((r for r in routes if match(r['pattern'], name)), None)
        if route:
            routed[name] = route['pattern']
        else:
            unrouted.append(name)
    return {'routes': routes, 'assumed_undefined': assumed, 'files': len(files),
            'routed': routed, 'unrouted': unrouted}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('trunk', type=Path, help='prepared and built Padavan trunk')
    parser.add_argument('--www', type=Path, help='served directory (default TRUNK/romfs/www)')
    parser.add_argument('--config', type=Path, help='firmware .config (default TRUNK/.config)')
    parser.add_argument('--define', action='append', default=[], help='extra defined macro, e.g. BOARD_WR1200JS')
    parser.add_argument('--report', type=Path)
    a = parser.parse_args()
    result = check(a.trunk, a.www or a.trunk / 'romfs/www', a.config or a.trunk / '.config', a.define)
    if a.report:
        a.report.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    if result['assumed_undefined']:
        print('Route conditions assumed undefined: ' + ', '.join(result['assumed_undefined']))
    if result['unrouted']:
        for name in result['unrouted']:
            print('FAIL no httpd route, served as 404: /' + name)
        sys.exit(1)
    print('PASS %d served /www files each match an effective httpd route' % result['files'])


if __name__ == '__main__':
    main()
