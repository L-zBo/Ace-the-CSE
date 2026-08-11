"""跨卷同题关联提示的浏览器验证。

页面是客户端渲染的，HTTP 200 证明不了内容出来了；关联数据又是 dynamic import
拉的，更要用真浏览器看一眼。

验证点：
  1. 有关联的题：提交后出现「这道题还考过 N 次」，条数与 links.json 一致
  2. 列表里的卷标签与 links.json 对得上（不是随便渲染了点什么）
  3. 关联条目能点进去，且落到的确实是那道题
  4. 未提交时不露出（避免被同题剧透）
  5. 无关联的题不显示这个模块
  6. 全程 0 console error

用法：python scripts/verify_related_appearances.py   （需先在 3000 端口起 dev）
"""
import io
import json
import os
import sys

from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

BASE = 'http://localhost:3000'
LINKS = 'src/data/index/cross-paper-links.json'
INDEX = 'src/data/index/question-index.json'

results = []
console_errors = []


def check(name, ok, detail=''):
    results.append((name, ok, detail))
    print(f'{"[PASS]" if ok else "[FAIL]"} {name}' + (f'  {detail}' if detail else ''))


def pick_targets():
    """挑一道有关联的可作答题 + 一道无关联的可作答题。"""
    links = json.load(open(LINKS, encoding='utf-8'))
    idx = json.load(open(INDEX, encoding='utf-8'))
    flag_unanswerable = idx['flags']['unanswerable']
    answerable = set()
    for row in idx['questions']:
        if not (row[3] & flag_unanswerable):
            answerable.add(row[0])

    linked_ids = {}
    for group in links['groups']:
        for qid, label_idx, qno in group:
            linked_ids[qid] = group

    with_link = None
    for group in links['groups']:
        # 选一组规模适中的，好顺带验证「展开其余 N 处」不出现
        if len(group) != 2:
            continue
        if all(q[0] in answerable for q in group):
            with_link = group
            break

    without_link = None
    for row in idx['questions']:
        qid = row[0]
        if qid in answerable and qid not in linked_ids and qid.startswith('national-'):
            without_link = qid
            break

    return links['paperLabels'], with_link, without_link


labels, group, solo_id = pick_targets()
target_id = group[0][0]
peer_id, peer_label_idx, peer_qno = group[1]
expected_peer_label = labels[peer_label_idx]
print(f'有关联的题：{target_id}（关联 {len(group) - 1} 处）')
print(f'  期望出处：{expected_peer_label} 第 {peer_qno} 题 -> {peer_id}')
print(f'无关联的题：{solo_id}\n')


def submit_first_option(page):
    opts = page.locator('[id^="option-"]')
    if opts.count() == 0:
        print('    [诊断] 没找到选项元素')
        return False
    opts.nth(0).click()
    page.wait_for_timeout(600)
    btn = page.locator('button:has-text("提交答案")')
    if btn.count() == 0:
        print('    [诊断] 没找到提交按钮')
        return False
    btn.first.click()
    page.wait_for_timeout(2000)
    if page.locator('button:has-text("提交答案")').count() > 0:
        print('    [诊断] 点击后仍停留在未提交态')
        return False
    return True


with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--no-proxy-server'])
    page = browser.new_page(viewport={'width': 1280, 'height': 1600})
    page.on('console', lambda m: console_errors.append(m.text)
            if m.type == 'error' else None)
    page.on('pageerror', lambda e: console_errors.append(f'pageerror: {e}'))

    # ---------- 1. 未提交时不露出 ----------
    # 必须等 networkidle：只等 load 的话 hydration 还没完成，
    # 点选项不会触发 React 的 onClick，后面全盘失真。
    page.goto(f'{BASE}/practice/{target_id}', wait_until='networkidle', timeout=180000)
    page.wait_for_timeout(2000)
    body = page.inner_text('body')
    check('答题页正常渲染', '题目加载中' not in body, f'页面 {len(body)} 字')
    check('未提交时不显示关联模块', '这道题还考过' not in body)

    # ---------- 2. 提交后露出 ----------
    ok = submit_first_option(page)
    check('能选中并提交', ok)
    page.wait_for_timeout(1500)

    panel = page.locator('section[aria-label="这道题的其他出处"]')
    check('提交后出现关联模块', panel.count() == 1, f'找到 {panel.count()} 个')

    if panel.count() == 1:
        text = panel.inner_text()
        check('标题条数正确',
              f'这道题还考过 {len(group) - 1} 次' in text,
              repr(text.splitlines()[0]))
        check('卷标签与数据一致', expected_peer_label in text,
              f'期望包含「{expected_peer_label}」')
        check('题号渲染出来', f'第 {peer_qno} 题' in text)
        rows = panel.locator('a[href^="/practice/"]')
        check('关联条目可点击', rows.count() == len(group) - 1,
              f'{rows.count()} 个链接')
        panel.scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        page.screenshot(path='data/tmp_verify_related.png', full_page=False)

        # ---------- 3. 点进去落到正确的题 ----------
        href = rows.nth(0).get_attribute('href')
        check('链接指向正确的题', href == f'/practice/{peer_id}', f'{href}')
        rows.nth(0).click()
        page.wait_for_timeout(3000)
        check('跳转后页面正常',
              '题目加载中' not in page.inner_text('body'),
              page.url.split('/')[-1])

    # ---------- 4. 无关联的题不显示 ----------
    page.goto(f'{BASE}/practice/{solo_id}', wait_until='networkidle', timeout=180000)
    page.wait_for_timeout(2000)
    submit_first_option(page)
    page.wait_for_timeout(1500)
    check('无关联的题不显示该模块',
          page.locator('section[aria-label="这道题的其他出处"]').count() == 0)

    browser.close()

check('0 console error', len(console_errors) == 0,
      '; '.join(console_errors[:3]) if console_errors else '')

passed = sum(1 for _, ok, _ in results if ok)
print(f'\n{passed}/{len(results)} 通过')
sys.exit(0 if passed == len(results) else 1)
