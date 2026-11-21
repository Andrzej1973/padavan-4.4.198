#!/usr/bin/env python3
"""Inventory exact-image Classic HTML/ASP surfaces without recording field values."""
import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path


class Surface(HTMLParser):
    def __init__(self):
        super().__init__()
        self.forms=[]
        self.names=set()
        self.links=set()
        self.document=False
    def handle_starttag(self, tag, attrs):
        attributes=dict(attrs)
        if tag in ('html','head','body'):
            self.document=True
        if tag=='form':
            self.forms.append({'method':attributes.get('method','get').lower(),
                               'action':attributes.get('action','')})
        if tag in ('input','select','textarea') and attributes.get('name'):
            self.names.add(attributes['name'])
        if tag in ('a','iframe'):
            value=attributes.get('href' if tag=='a' else 'src','')
            if value and not value.startswith(('http:','https:','javascript:','#')):
                self.links.add(value)


def inventory(www, revision, image_hash):
    pages=[]
    for path in sorted(www.rglob('*')):
        if path.is_symlink() or not path.is_file() or path.suffix.lower() not in ('.asp','.htm','.html'):
            continue
        relative=path.relative_to(www).as_posix()
        if relative.startswith('modern/'):
            continue
        content=path.read_bytes()
        text=content.decode('utf-8',errors='replace')
        parser=Surface()
        parser.feed(text)
        pages.append({'classic':relative,'bytes':len(content),'sha256':hashlib.sha256(content).hexdigest(),
                      'kind':'document' if parser.document else 'fragment-or-handler',
                      'forms':parser.forms,'field_names':sorted(parser.names),
                      'local_links':sorted(parser.links),
                      'modern_route':None,'modern_design':'pending-page-review',
                      'modern_backend':'not-accepted','host_verified':False,
                      'target_verified':False,'runtime_verified':False})
    return {'source_sha':revision,'image_sha256':image_hash,
            'scope':'Exact image Classic surfaces; inventory is not hardware capability or Modern completion proof',
            'completion_rule':'Every supported Classic function needs Modern design, existing backend mapping, target/image and separately authorized runtime evidence. Helpers require explicit parent mapping; no silent omission.',
            'page_count':len(pages),'document_count':sum(p['kind']=='document' for p in pages),'pages':pages}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--www',type=Path,required=True)
    parser.add_argument('--source-sha',required=True)
    parser.add_argument('--image-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--matrix',type=Path,required=True)
    args=parser.parse_args()
    if not re.fullmatch('[0-9a-f]{40}',args.source_sha) or not re.fullmatch('[0-9a-f]{64}',args.image_sha256):
        parser.error('exact source SHA and image SHA256 required')
    result=inventory(args.www,args.source_sha,args.image_sha256)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    rows=['# WR1200JS full Modern page coverage','',
          'Owner requires every supported page and subpage, not only the dashboard.',
          'Classic links and generic section placeholders do not count as complete Modern pages.',
          'All rows start unaccepted pending individual functional mapping. Existing shell/DEMO evidence remains separate.',
          f"Source: `{args.source_sha}`; image: `{args.image_sha256}`.",'',
          '| Classic image path | Surface | Forms | Modern mapping / design | Backend / host / target / device |',
          '|---|---|---:|---|---|']
    for page in result['pages']:
        rows.append(f"| `{page['classic']}` | {page['kind']} | {len(page['forms'])} | pending review | not accepted |")
    args.matrix.write_text('\n'.join(rows)+'\n')
    print(f"Inventoried {result['page_count']} Classic surfaces ({result['document_count']} documents); no completion claim")
