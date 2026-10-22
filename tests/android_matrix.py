"""Android Chromium matrix: touchscreen, responsive layout, CRUD, offline and downloads."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from playwright.sync_api import sync_playwright, expect
import os

ROOT=Path(__file__).resolve().parents[1]
class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

def page_check(page,width):
    assert page.locator('.main-tab').count()==4
    for name in ('week','shopping','finance','settings'):
        page.locator(f'.main-tab[data-page="{name}"]').tap()
        bounds=page.evaluate('''() => ({vw:window.innerWidth,doc:document.documentElement.scrollWidth,body:document.body.scrollWidth})''')
        assert bounds['doc']<=bounds['vw']+1 and bounds['body']<=bounds['vw']+1,(width,name,bounds)
    hit=page.evaluate('''() => ({tabs:[...document.querySelectorAll('.main-tab')].map(e=>e.getBoundingClientRect().height),buttons:[...document.querySelectorAll('.manager-row button,.section-row button')].map(e=>Math.min(e.getBoundingClientRect().width,e.getBoundingClientRect().height)),manager:[...document.querySelectorAll('.manager-row .row-main')].slice(0,2).map(e=>e.getBoundingClientRect().width)})''')
    assert min(hit['tabs'])>=43,(width,hit)
    assert min(hit['buttons'])>=43,(width,hit)
    assert min(hit['manager'])>=110,(width,hit)

def full_flow(page,real_http):
    page.locator('.main-tab[data-page=settings]').tap()
    page.locator('#newSectionTitle').fill('Android test')
    page.locator('#addSectionForm button[type=submit]').tap()
    sec=page.locator('#taskSection option').filter(has_text='Android test').get_attribute('value')
    assert sec
    page.locator('#taskTitle').fill('Touch task')
    page.locator('#taskSection').select_option(sec)
    page.locator('#taskTime').fill('15:30')
    page.locator('#taskRemind').check()
    page.locator('#taskForm button[type=submit]').tap()
    expect(page.locator('#taskManager').get_by_text('Touch task')).to_be_visible()
    page.locator('.main-tab[data-page=week]').tap()
    row=page.locator('.task-row').filter(has_text='Touch task')
    expect(row).to_be_visible()
    assert row.locator('.check-square').evaluate('(e)=>Math.min(e.getBoundingClientRect().height,e.getBoundingClientRect().width)')>=43
    row.locator('button.bell').tap()
    expect(row.locator('button.bell')).to_have_attribute('aria-pressed','false')
    row.locator('input[type=checkbox]').check()
    expect(row.locator('input[type=checkbox]')).to_be_checked()
    page.locator('.main-tab[data-page=shopping]').tap()
    page.locator('#shoppingTitle').fill('Rice')
    page.locator('#shoppingRemind').check()
    page.locator('#shoppingForm button[type=submit]').tap()
    expect(page.locator('.shop-row').filter(has_text='Rice')).to_be_visible()
    page.locator('.main-tab[data-page=finance]').tap()
    page.locator('#financeAmount').fill('120.50')
    page.locator('#financeCategory').fill('Groceries')
    page.locator('#financeForm button[type=submit]').tap()
    expect(page.locator('#ledgerItems').get_by_text('Groceries')).to_be_visible()
    with page.expect_download() as transfer:page.locator('#financeCSV').tap()
    assert transfer.value.suggested_filename.endswith('.csv')
    page.locator('.main-tab[data-page=settings]').tap()
    with page.expect_download() as transfer:page.locator('#backupData').tap()
    assert transfer.value.suggested_filename.endswith('.json')
    page.locator('#testReminder').tap()
    expect(page.locator('#reminderOverlay')).to_be_visible()
    page.locator('#reminderDismiss').tap()
    expect(page.locator('#reminderOverlay')).to_be_hidden()
    if real_http:
        page.reload()
        page.locator('.main-tab[data-page=week]').tap()
        expect(page.locator('.task-row').filter(has_text='Touch task')).to_be_visible()
        page.locator('.main-tab[data-page=finance]').tap()
        expect(page.locator('#ledgerItems').get_by_text('Groceries')).to_be_visible()

def inline_load(page):
    from bs4 import BeautifulSoup
    soup=BeautifulSoup((ROOT/'index.html').read_text(encoding='utf-8'),'html.parser')
    for el in soup.select('script,link[rel=stylesheet]'):el.decompose()
    page.set_content(str(soup))
    page.add_style_tag(content=(ROOT/'styles.css').read_text(encoding='utf-8'))
    page.evaluate('''() => {const mem={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>mem[k]??null,setItem:(k,v)=>mem[k]=String(v),removeItem:k=>delete mem[k]}})}''')
    for file in ('model.js','config.js','app.js'):
        page.add_script_tag(content=(ROOT/file).read_text(encoding='utf-8'))

def main():
    inline=os.getenv('ANDROID_TEST_INLINE')=='1'
    server=None
    if not inline:
        server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT)))
        Thread(target=server.serve_forever,daemon=True).start()
    try:
        with sync_playwright() as driver:
            browser=driver.chromium.launch(headless=True,args=['--no-sandbox'],**({'executable_path':'/usr/bin/chromium'} if inline else {}))
            for width,height in [(280,650),(320,740),(360,780),(393,852),(412,915),(768,1024)]:
                context=browser.new_context(viewport={'width':width,'height':height},is_mobile=True,has_touch=True,device_scale_factor=2,accept_downloads=True)
                page=context.new_page();errors=[]
                page.on('pageerror',lambda e:errors.append(str(e)))
                if inline:inline_load(page)
                else:page.goto(f'http://127.0.0.1:{server.server_port}/index.html',wait_until='load')
                page_check(page,width)
                if width==360:
                    full_flow(page,not inline)
                    if not inline:
                        page.evaluate('() => navigator.serviceWorker.ready')
                        page.reload()
                        expect(page.locator('.task-row').first).to_be_visible()
                        context.set_offline(True)
                        page.reload()
                        expect(page.locator('.task-row').first).to_be_visible()
                        context.set_offline(False)
                assert not errors,(width,errors)
                print(f'PASS Android emulation {width}px: navigation, touch targets, layout'+(', CRUD, export, notification, persistence, offline' if width==360 else ''),flush=True)
                context.close()
            browser.close()
    finally:
        if server:server.shutdown();server.server_close()

if __name__=='__main__': main()