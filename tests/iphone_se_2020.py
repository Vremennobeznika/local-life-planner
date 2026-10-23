"""iPhone SE (2020), 375x667 @2x, WebKit (Safari engine) installability and workflows."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright, expect
import json

ROOT=Path(__file__).resolve().parents[1]
class Quiet(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass

def check_inside(page):
    return page.evaluate("""() => {
      const w=window.innerWidth, boxes=[...document.querySelectorAll('input:not([type=hidden]), select, button')].filter(e=>{
        const style=getComputedStyle(e);return style.display!=='none'&&e.getClientRects().length&&e.closest('.page')?.classList.contains('active')
      });
      return {width:w,scroll:document.documentElement.scrollWidth, failures:boxes.map(e=>{
        const r=e.getBoundingClientRect();return {name:e.id||e.textContent.slice(0,20),left:r.left,right:r.right,height:r.height}
      }).filter(x=>x.left < -2||x.right>w+2)};
    }""")

def test():
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(ROOT)))
    Thread(target=server.serve_forever,daemon=True).start()
    try:
      with sync_playwright() as p:
        browser=p.webkit.launch(headless=True)
        context=browser.new_context(viewport={'width':375,'height':667},device_scale_factor=2,
          is_mobile=True,has_touch=True,accept_downloads=True,locale='ru-RU')
        page=context.new_page()
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.goto(f'http://127.0.0.1:{server.server_port}/index.html')
        for section in ['week','shopping','finance','settings']:
          page.locator('.main-tab[data-page="'+section+'"]').tap()
          geometry=check_inside(page)
          assert geometry['scroll']<=geometry['width']+2,(section,geometry)
          assert not geometry['failures'],(section,geometry['failures'])
          assert page.locator('.main-tabs').is_visible()
        page.locator('#taskMode').select_option('once')
        page.locator('#taskTitle').fill('Дело на другую дату')
        page.locator('#taskTime').fill('16:30')
        page.locator('#taskDate').fill('2026-11-05')
        page.locator('#taskRemind').check()
        page.locator('#taskForm button[type=submit]').tap()
        expect(page.locator('#taskManager')).to_contain_text('Дело на другую дату')
        page.locator('.main-tab[data-page=shopping]').tap()
        page.locator('#shoppingTitle').fill('Хлеб')
        page.locator('#shoppingQty').fill('2 шт')
        page.locator('#shoppingForm button[type=submit]').tap()
        expect(page.locator('#shoppingItems')).to_contain_text('Хлеб')
        page.locator('.main-tab[data-page=finance]').tap()
        page.locator('#financeAmount').fill('140.50')
        page.locator('#financeCategory').fill('Покупки')
        page.locator('#financeForm button[type=submit]').tap()
        expect(page.locator('#ledgerItems')).to_contain_text('Покупки')
        page.locator('.main-tab[data-page=settings]').tap()
        with page.expect_download() as d:
          page.locator('#backupData').tap()
        assert d.value.suggested_filename.endswith('.json')
        content=json.loads(Path(d.value.path()).read_text(encoding='utf-8'))
        assert any(x['title']=='Дело на другую дату' and x.get('date')=='2026-11-05' for x in content.get('data',content).get('tasks',[])), list(content.keys())
        page.reload()
        page.locator('.main-tab[data-page=settings]').tap()
        expect(page.locator('#taskManager')).to_contain_text('Дело на другую дату')
        page.locator('.main-tab[data-page=shopping]').tap()
        expect(page.locator('#shoppingItems')).to_contain_text('Хлеб')
        page.locator('.main-tab[data-page=finance]').tap()
        expect(page.locator('#ledgerItems')).to_contain_text('Покупки')
        # iOS WebKit may limit Service Worker and notification support in emulation.
        manifest=json.loads((ROOT/'manifest.webmanifest').read_text(encoding='utf-8'))
        assert manifest['display']=='standalone'
        assert manifest['start_url'].startswith('./')
        assert not errors,errors
        print('PASS iPhone SE 2020 WebKit 375x667 @2x: no overflow, tabs, one-time tasks, reminders, shopping, finances, JSON export and persistence',flush=True)
        context.close()
        browser.close()
    finally:
      server.shutdown();server.server_close()

if __name__=='__main__':test()
