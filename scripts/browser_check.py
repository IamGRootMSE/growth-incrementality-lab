"""Exercise the real static site at desktop/mobile sizes with no external service."""
import functools
import http.server
import json
import os
import threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
local_browser=ROOT/'work/browsers'
if local_browser.exists():os.environ.setdefault('PLAYWRIGHT_BROWSERS_PATH',str(local_browser))

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

def run():
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'outputs/site')))
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    url=f'http://127.0.0.1:{server.server_port}'
    output=ROOT/'outputs/screenshots';output.mkdir(parents=True,exist_ok=True)
    errors=[];checks=[]
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            page=browser.new_page(viewport={'width':1440,'height':1050},device_scale_factor=1)
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(url,wait_until='networkidle')
            assert page.locator('#metrics .metric').count()==4
            assert page.locator('svg.chart').count()==3
            assert '100.1' in page.locator('#scenario-conversions').inner_text()
            page.screenshot(path=str(output/'desktop.png'),full_page=True)
            page.locator('#simulator').screenshot(path=str(output/'budget-lab.png'))
            # Browser calculation vs independently evaluated Python arithmetic.
            r=json.loads((ROOT/'outputs/analysis/results.json').read_text())
            for policy in r['curves']:
                for depth in [0,5,20,50,100]:
                    params={'policy':policy,'depth':depth,'audience':100000,'cost':.2,'value':100,'budget':100000}
                    s=page.evaluate('(p)=>computeScenario(LAB_RESULTS,p)',params)
                    point=r['curves'][policy]['points'][depth//5]
                    assert abs(s['increment']-100000*point['estimate'])<1e-8
                    assert abs(s['net']-(10000000*point['estimate']-int(100000*depth/100)*.2))<1e-8
                    assert abs(s['netLow']-(10000000*point['low']-int(100000*depth/100)*.2))<1e-8
            checks.append('20 browser/Python policy-depth scenario reconciliations')
            page.locator('#budget').fill('999')
            assert '0% reach' in page.locator('#scenario-reach').inner_text()
            page.locator('#budget').fill('1000')
            assert '5% reach' in page.locator('#scenario-reach').inner_text()
            page.locator('#cost').fill('0')
            assert '20% reach' in page.locator('#scenario-reach').inner_text()
            page.locator('#audience').fill('0')
            assert 'Enter valid' in page.locator('#scenario-error').inner_text()
            assert page.locator('#scenario-conversions').inner_text()=='—'
            checks.append('Budget boundary, zero cost, invalid audience and stale-output clearing')
            page.goto(url,wait_until='networkidle')
            page.locator('#depth').focus();page.keyboard.press('ArrowRight')
            assert page.locator('#depth-label').inner_text()=='25%'
            checks.append('Keyboard targeting-depth interaction')
            for width,height,name in [(1440,1050,'desktop'),(390,844,'mobile')]:
                page.set_viewport_size({'width':width,'height':height})
                for route in ['index.html','methodology.html','provenance.html','decision-memo.html','walkthrough.html','interview-guide.html','resume-bullets.html']:
                    response=page.goto(url+'/'+route,wait_until='networkidle')
                    assert response.status==200
                    overflow=page.evaluate('''() => [...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>innerWidth+1).map(e=>({tag:e.tagName,id:e.id,class:e.className,right:e.getBoundingClientRect().right})).slice(0,20)''')
                    if page.evaluate('document.documentElement.scrollWidth > window.innerWidth'):
                        page.screenshot(path=str(output/'overflow-debug.png'),full_page=True)
                        raise AssertionError((name,route,overflow))
                page.goto(url,wait_until='networkidle')
                if name=='mobile':
                    page.screenshot(path=str(output/'mobile.png'),full_page=True)
                    page.screenshot(path=str(output/'mobile-viewport.png'))
                    page.locator('#targeting').screenshot(path=str(output/'mobile-targeting.png'))
            checks.append('Seven routes at 1440px and 390px; no page-level overflow')
            page.goto(url+'/decision-memo.html',wait_until='networkidle')
            page.set_viewport_size({'width':900,'height':1200})
            page.screenshot(path=str(output/'decision-memo.png'),full_page=True)
            browser.close()
    finally:
        server.shutdown();server.server_close()
    assert not errors,errors
    checks.append('No browser JavaScript exceptions')
    result={'status':'passed','checks':checks,'screenshots':['desktop.png','mobile.png','budget-lab.png','decision-memo.png']}
    (ROOT/'outputs/analysis/browser-validation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':run()
