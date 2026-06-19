"""D-16 L-3b 抓 aipta.com article → 解析为 questions JSON

用法：
  python scripts/d16_fetch_aipta.py --fetch 2241          # 抓单 article
  python scripts/d16_fetch_aipta.py --fetch 2241 --force  # 强制重抓
  python scripts/d16_fetch_aipta.py --fetch-all           # 抓预设清单

输出：data/aipta_cache/article_{id}.json
  {
    "article_id": 2241,
    "title": "2020甘肃事业单位联考真题及答案解析（C类）",
    "questions": [
      {"qn": 1, "stem": "...", "options": [{"label":"A","content":"..."}, ...]}
    ]
  }
"""
import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

BASE = 'https://www.aipta.com'
CACHE_DIR = Path('data/aipta_cache')
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
}

# 题号正则：行首数字 + 点 / 顿号（如 "1." "23." "100、"）
QN_PAT = re.compile(r'^\s*(\d{1,3})\s*[\.、．]\s*')
# 选项正则：行首字母 + 点 / 顿号
OPT_PAT = re.compile(r'^\s*([A-D])\s*[\.、．]\s*')


def http_get(url: str, retries: int = 3, sleep: float = 1.5) -> str:
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=25) as resp:
                raw = resp.read()
            # 自动识别编码
            for enc in ('utf-8', 'gb18030', 'gbk'):
                try:
                    return raw.decode(enc)
                except UnicodeDecodeError:
                    continue
            return raw.decode('utf-8', errors='replace')
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last = e
            time.sleep(sleep * (i + 1))
    raise RuntimeError(f'GET {url} 失败: {last}')


def parse_article(html: str, article_id: int) -> dict:
    """从 article HTML 提取 questions list。

    aipta 文章正文在 <div class='article-content'> 或类似容器里，
    内容是大量 <p> 标签的纯文本，按行解析题号 / 选项 anchor。
    """
    soup = BeautifulSoup(html, 'lxml')
    title = (soup.find('title').get_text() if soup.find('title') else '').strip()
    # 拿最大一个含 "题" / 模块标记的容器
    candidates = soup.find_all(['div', 'article'])
    content_blob = ''
    best_score = 0
    for c in candidates:
        txt = c.get_text('\n', strip=False)
        if not txt or len(txt) < 1000:
            continue
        # 看出现多少次"第X题" / "A." / "B." 这种 anchor
        score = (
            len(re.findall(r'\n[A-D][\.、]', txt))
            + len(re.findall(r'\n\d{1,3}[\.、]', txt))
        )
        if score > best_score:
            best_score = score
            content_blob = txt
    if not content_blob:
        # 退而求其次：body
        content_blob = soup.get_text('\n', strip=False)

    # 按行解析
    lines = [l.rstrip() for l in content_blob.split('\n') if l.strip()]
    questions = []
    cur = None  # {'qn', 'stem_parts': [], 'options': {A,B,C,D}, 'pending_letter'}

    def push_cur():
        nonlocal cur
        if cur and cur.get('qn') is not None:
            opts = []
            for L in 'ABCD':
                if L in cur['options']:
                    opts.append({'label': L, 'content': cur['options'][L].strip()})
            questions.append({
                'qn': cur['qn'],
                'stem': ' '.join(cur['stem_parts']).strip(),
                'options': opts,
            })
        cur = None

    for line in lines:
        m_q = QN_PAT.match(line)
        m_o = OPT_PAT.match(line)
        if m_q and not m_o:
            # 题号开头：先推前一题
            push_cur()
            qn = int(m_q.group(1))
            rest = QN_PAT.sub('', line).strip()
            cur = {'qn': qn, 'stem_parts': [rest] if rest else [], 'options': {}, 'pending_letter': None}
        elif m_o and cur is not None:
            letter = m_o.group(1)
            rest = OPT_PAT.sub('', line).strip()
            cur['options'][letter] = rest
            cur['pending_letter'] = letter
        elif cur is not None:
            # 续行：归到 pending_letter 或 stem
            pl = cur.get('pending_letter')
            if pl and pl in cur['options']:
                cur['options'][pl] = (cur['options'][pl] + ' ' + line.strip()).strip()
            else:
                cur['stem_parts'].append(line.strip())
        # 否则忽略
    push_cur()

    # 仅保留题号合理 (1-200) 且有题干/选项的
    valid = [q for q in questions if 1 <= q['qn'] <= 200 and (q['stem'] or q['options'])]

    return {
        'article_id': article_id,
        'url': f'{BASE}/article/{article_id}.html',
        'title': title,
        'question_count': len(valid),
        'questions': valid,
    }


def fetch_article(article_id: int, force: bool = False) -> dict:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    fp = CACHE_DIR / f'article_{article_id}.json'
    if fp.exists() and not force:
        return json.loads(fp.read_text(encoding='utf-8'))
    url = f'{BASE}/article/{article_id}.html'
    print(f'[fetch] {url}')
    html = http_get(url)
    data = parse_article(html, article_id)
    fp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'  -> {fp}  questions={data["question_count"]}  title={data["title"][:60]}')
    return data


# institution 联考 aipta paper 已知映射（甘肃为主，2022 待补）
INST_PAPERS = {
    'institution_2020_a': [2239, 2244],
    'institution_2020_b': [2240],
    'institution_2020_c': [2241],
    'institution_2020_d': [2242],
    'institution_2020_e': [2243],
    'institution_2021_a': [2245],
    'institution_2021_b': [2246],
    'institution_2021_c': [2247],
    'institution_2021_e': [2248],
    # 2022 BCE 待人工补 article id
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--fetch', type=int, help='抓单 article ID')
    ap.add_argument('--fetch-all', action='store_true', help='按 INST_PAPERS 抓预设清单')
    ap.add_argument('--force', action='store_true', help='已 cache 也重抓')
    args = ap.parse_args()

    if args.fetch:
        fetch_article(args.fetch, force=args.force)
    elif args.fetch_all:
        ids = []
        for v in INST_PAPERS.values():
            ids.extend(v)
        ids = sorted(set(ids))
        print(f'共 {len(ids)} 个 article 待抓')
        for aid in ids:
            try:
                fetch_article(aid, force=args.force)
                time.sleep(2)  # 礼貌延迟
            except Exception as e:
                print(f'  !! {aid} 失败: {e}')
    else:
        ap.print_help()


if __name__ == '__main__':
    main()
