"""Check rendered synthetic report against executed JSON at two viewports."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]


def main():
    report=ROOT/'outputs/experiment'
    data=json.loads((report/'results.json').read_text(encoding='utf-8'))
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch()
        page=browser.new_page()
        page.on('pageerror',lambda e:errors.append(str(e)))
        for name,width,height in [('desktop',1440,1000),('mobile',390,844)]:
            page.set_viewport_size(dict(width=width,height=height))
            page.goto((report/'index.html').as_uri())
            assert 'SYNTHETIC' in page.locator('body').inner_text()
            assert page.locator('h1').count()==1
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
            for scenario,result in data['scenarios'].items():
                section=page.locator('section').filter(has=page.get_by_role('heading',name=scenario.replace('_',' ').title(),exact=True))
                assert result['decision'] in section.inner_text()
                for metric,m in result['metrics'].items():
                    scale=100 if metric=='converted' else 1
                    assert f'{m["estimate"]*scale:+.3f}' in section.inner_text()
            page.screenshot(path=str(report/f'{name}.png'),full_page=True)
            page.get_by_role('link',name='executed JSON evidence').click()
            assert 'input_sha256' in page.locator('body').inner_text()
        browser.close()
    assert not errors,errors
    receipt=dict(status='passed',viewports=[1440,390],checks=['synthetic label','all decisions and estimates match JSON','no page overflow','evidence link','no JS errors'])
    (report/'browser-validation.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(receipt))


if __name__=='__main__':main()
