"""重构后功能验证：确认懒加载没有破坏页面实际渲染。

页面是客户端渲染的，HTTP 200 只能证明服务端没炸，证明不了内容出来了。
这里用真实浏览器跑一遍关键路径。

用法：python scripts/verify_lazy_loader.py   （需先在 3000 端口起 dev）
"""
import io
import sys

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = 'http://localhost:3000'
QID = 'national-xingce-changshi-2024-dishi-001'

results = []
console_errors = []


def check(name, ok, detail=''):
    results.append((name, ok, detail))
    print(f'{"✅" if ok else "❌"} {name}' + (f'  {detail}' if detail else ''))


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 1400})
    page.on('console', lambda m: console_errors.append(m.text)
            if m.type == 'error' else None)
    page.on('pageerror', lambda e: console_errors.append(f'pageerror: {e}'))

    # ---------- 答题页 ----------
    page.goto(f'{BASE}/practice/{QID}', wait_until='networkidle', timeout=180000)
    page.wait_for_timeout(1500)

    body = page.inner_text('body')
    check('答题页不再停留在「题目加载中」', '题目加载中' not in body)

    opts = page.locator('[id^="option-"]')
    n = opts.count()
    check('四个选项渲染出来', n == 4, f'实际 {n} 个')

    labels = [opts.nth(i).inner_text()[:1] for i in range(n)]
    check('选项 label 齐全', sorted(labels) == ['A', 'B', 'C', 'D'], f'{labels}')

    stem = page.locator('main, article, body').first.inner_text()
    check('题干有实质内容', len(stem) > 200, f'页面文本 {len(stem)} 字')

    page.screenshot(path='data/tmp_verify_question.png', full_page=False)

    # ---------- 选中并提交 ----------
    opts.nth(0).click()
    page.wait_for_timeout(400)
    submit = page.locator('button', has_text='提交').first
    if submit.count():
        submit.click()
        page.wait_for_timeout(1200)
        after = page.inner_text('body')
        check('提交后出现解析区', ('解析' in after or '正确答案' in after))
    else:
        check('找到提交按钮', False)

    # ---------- 列表页 ----------
    page.goto(f'{BASE}/practice', wait_until='networkidle', timeout=180000)
    page.wait_for_timeout(1200)
    txt = page.inner_text('body')
    check('练习选择页有题量统计', any(c.isdigit() for c in txt) and len(txt) > 300)

    # ---------- 错题本 ----------
    page.goto(f'{BASE}/review', wait_until='networkidle', timeout=180000)
    page.wait_for_timeout(1200)
    check('错题本正常渲染', '错题本' in page.inner_text('body'))

    # ---------- 模拟考试列表 ----------
    page.goto(f'{BASE}/exam', wait_until='networkidle', timeout=180000)
    page.wait_for_timeout(1200)
    check('模拟考试页正常渲染', '模拟考试' in page.inner_text('body'))

    browser.close()

real_errors = [e for e in console_errors if 'favicon' not in e.lower()]
print()
check('无 console error', len(real_errors) == 0, f'{len(real_errors)} 条')
for e in real_errors[:5]:
    print('    ', e[:200])

failed = [r for r in results if not r[1]]
print(f'\n通过 {len(results) - len(failed)}/{len(results)}')
sys.exit(1 if failed else 0)
