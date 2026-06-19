"""D-17/web-design audit: 启 next dev + 跑首页 / 题详情 / 题库列表 screenshot + console log
保存到 data/screenshots/d17_*.png，console 错误存 data/screenshots/console.log
"""
import os, sys, json
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path('F:/VsCodeproject/Ace-the-CSE/data/screenshots')
OUT.mkdir(parents=True, exist_ok=True)

console_log = []

def on_console(msg):
    if msg.type in ('error', 'warning'):
        console_log.append(f'[{msg.type.upper()}] {msg.text}')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(viewport={'width': 1280, 'height': 800})
    page = context.new_page()
    page.on('console', on_console)
    page.on('pageerror', lambda err: console_log.append(f'[PAGEERROR] {err}'))

    targets = [
        ('home', 'http://localhost:3000/'),
        ('practice', 'http://localhost:3000/practice'),
    ]
    results = {}
    for name, url in targets:
        try:
            page.goto(url, wait_until='commit', timeout=15000)
            # 等关键元素：首页用 h1，practice 用任何 main 内容
            sel = 'h1' if name == 'home' else 'main'
            page.wait_for_selector(sel, timeout=120000)
            page.wait_for_timeout(2500)  # framer-motion 进场动画 + JS hydration 落定
            shot = OUT / f'd17_{name}.png'
            page.screenshot(path=str(shot), full_page=False)
            # 检查 hero / Bo logo 颜色（getBoundingClientRect + getComputedStyle）
            inspect = page.evaluate('''() => {
                const bo = document.querySelector('div[class*="gradient-mo-seal"]') || document.querySelector('.gradient-mo-seal');
                const exam1 = document.querySelector('a[href="/practice/national"]');
                const fontBody = window.getComputedStyle(document.body).fontFamily;
                const fontH1 = document.querySelector('h1') ? window.getComputedStyle(document.querySelector('h1')).fontFamily : null;
                return {
                    boHasGradient: bo ? window.getComputedStyle(bo).background.slice(0,200) : 'MISSING',
                    examNationalBg: exam1 ? window.getComputedStyle(exam1).background.slice(0,200) : 'MISSING',
                    bodyFont: fontBody,
                    h1Font: fontH1,
                };
            }''')
            results[name] = {'ok': True, 'inspect': inspect}
            print(f'OK {name}: {shot}')
        except Exception as e:
            results[name] = {'ok': False, 'err': str(e)}
            print(f'FAIL {name}: {e}')

    (OUT / 'd17_inspect.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    (OUT / 'd17_console.log').write_text('\n'.join(console_log) or '(no errors/warnings)', encoding='utf-8')
    browser.close()

print(f'\n== console errors/warnings ({len(console_log)} entries) ==')
for line in console_log[:30]:
    print(line)
