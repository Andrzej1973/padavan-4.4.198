"""Use the checked actual shared-header probe prefix for a device diagnostic."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('header_probe', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
source = a.header_probe.read_text(encoding='utf-8')
anchor = 'int main(void){return 0;}'
if source.count(anchor) != 1:
    raise SystemExit('Shared header probe main changed')
body = (Path(__file__).resolve().parent / 'radio-diagnostic.inc').read_text(encoding='utf-8')
a.output.write_text(source.replace(anchor, body), encoding='utf-8')
