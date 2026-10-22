"""Headless Chromium smoke test. Works without HTTP access in sandbox via inline assets."""
import sys
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright, expect

BASE=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
OUT=Path('/mnt/data/life_previews'); OUT.mkdir(exist_ok=True)

with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for width,height in [(390,844),(320,740),(1280,900)]:
  page=browser.new_page(viewport={'width':width,'height':height},accept_downloads=True,device_scale_factor=1)
  errors=[];page.on('pageerror',lambda e: errors.append(str(e)))
  soup=BeautifulSoup((BASE/'index.html').read_text(),'html.parser')
  for node in soup.select('script,link[rel=stylesheet]'):node.decompose()
  page.set_content(str(soup))
  page.add_style_tag(content=(BASE/'styles.css').read_text())
  page.evaluate("() => {const mem={};Object.defineProperty(window,'localStorage',{configurable:true,value:{getItem:k=>mem[k]??null,setItem:(k,v)=>mem[k]=String(v),removeItem:k=>delete mem[k]}})}")
  for script in ('model.js','config.js','app.js'):page.add_script_tag(content=(BASE/script).read_text())
  expect(page.locator('.task-row').first).to_be_visible()
  assert len(page.locator('.main-tab').all_text_contents())==4
  assert not page.evaluate('document.documentElement.scrollWidth>window.innerWidth'),f'week overflow {BASE} {width}'
  page.screenshot(path=str(OUT/(BASE.name+f'-{width}-week.png')),full_page=True)
  page.locator('button[data-page="settings"]').click()
  assert page.locator('#sectionManager .section-row').count()>=3
  assert not page.evaluate('document.documentElement.scrollWidth>window.innerWidth'),f'settings overflow {BASE} {width}'
  # Add a routine section and schedule item from the dedicated settings page.
  page.locator('#newSectionTitle').fill('Тестовый раздел')
  page.locator('#newSectionType').select_option('routine')
  page.locator('#addSectionForm button[type="submit"]').click()
  options=page.locator('#taskSection option').all_text_contents()
  assert 'Тестовый раздел' in options
  page.locator('#taskTitle').fill('Проверить тестовый пункт')
  page.locator('#taskTime').fill('16:40')
  selectval=page.locator('#taskSection option').filter(has_text='Тестовый раздел').get_attribute('value')
  page.locator('#taskSection').select_option(selectval)
  page.locator('#taskRemind').check()
  page.locator('#taskForm button[type="submit"]').click()
  assert page.locator('#taskManager').get_by_text('Проверить тестовый пункт').count()==1
  # One-time appointment created in the same settings editor.
  page.locator('#taskMode').select_option('once')
  assert page.locator('#taskDateWrap').is_visible() and page.locator('#taskDaysWrap').is_hidden()
  page.locator('#taskTitle').fill('Разовое дело на сегодня')
  page.locator('#taskForm button[type="submit"]').click()
  assert page.locator('#taskManager').get_by_text('Разовое дело на сегодня').count()==1
  page.locator('button[data-page="week"]').click()
  row=page.locator('.task-row').filter(has_text='Проверить тестовый пункт')
  assert row.count()==1
  bell=row.locator('button.bell')
  assert bell.get_attribute('aria-pressed')=='true'
  bell.click()
  row=page.locator('.task-row').filter(has_text='Проверить тестовый пункт')
  assert row.locator('button.bell').get_attribute('aria-pressed')=='false'
  row.locator('input[type=checkbox]').check()
  assert row.locator('input[type=checkbox]').is_checked()
  page.locator('button[data-page="shopping"]').click()
  assert not page.evaluate('document.documentElement.scrollWidth>window.innerWidth'),f'shopping overflow {BASE} {width}'
  page.locator('#shoppingTitle').fill('Тестовые продукты')
  page.locator('#shoppingQty').fill('2 шт.')
  page.locator('#shoppingRemind').check()
  page.locator('#shoppingForm button[type="submit"]').click()
  shop=page.locator('.shop-row').filter(has_text='Тестовые продукты')
  assert shop.count()==1 and shop.locator('button.bell').get_attribute('aria-pressed')=='true'
  shop.locator('input[type=checkbox]').check()
  page.locator('button[data-page="finance"]').click()
  assert not page.evaluate('document.documentElement.scrollWidth>window.innerWidth'),f'finance overflow {BASE} {width}'
  page.locator('#financeAmount').fill('120.50')
  page.locator('#financeCategory').fill('Тест расходы')
  page.locator('#financeForm button[type="submit"]').click()
  assert page.locator('#ledgerItems').get_by_text('Тест расходы').count()==1
  with page.expect_download() as download_ctx:page.locator('#financeCSV').click()
  file=download_ctx.value
  assert file.suggested_filename.endswith('.csv')
  from pathlib import Path as _Path
  assert 'Тест расходы' in _Path(file.path()).read_text(encoding='utf-8-sig')
  page.locator('button[data-page="settings"]').click()
  page.locator('#testReminder').click()
  assert page.locator('#reminderOverlay').is_visible()
  page.locator('#reminderDismiss').click()
  assert page.locator('#reminderOverlay').is_hidden()
  if width==390:
   page.screenshot(path=str(OUT/(BASE.name+'-390-settings.png')),full_page=True)
  assert not errors,(BASE.name,width,errors)
  print(f'PASS {BASE.name} {width}px: navigation/settings/routine/bell/checklist/finance/reminder; no JS errors or horizontal overflow')
  page.close()
 browser.close()
