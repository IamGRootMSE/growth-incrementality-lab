import json
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit,unquote
from scripts.build_site import build

class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.ids=set()
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.add(a['id'])
        for key in ['href','src']:
            if key in a:self.links.append(a[key])

def test_build_is_portable_and_internal_links_resolve(tmp_path):
    out=build(tmp_path/'site')
    for page in out.glob('*.html'):
        p=Links();p.feed(page.read_text(encoding='utf-8'))
        for link in p.links:
            u=urlsplit(link)
            if u.scheme or u.netloc:continue
            target=page.parent/unquote(u.path) if u.path else page
            assert target.exists(),(page.name,link)
            if u.fragment and target.suffix=='.html':
                dest=Links();dest.feed(target.read_text(encoding='utf-8'))
                assert u.fragment in dest.ids,(page.name,link)
    r=json.loads((out/'data/results.json').read_text())
    assert (out/'data/results.js').read_text().startswith('window.LAB_RESULTS = ')
    assert r['mode']=='empirical'
