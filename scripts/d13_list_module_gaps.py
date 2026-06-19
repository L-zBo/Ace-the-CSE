"""D-13 列各模块缺题文件清单（按文件归类，便于一卷一卷救）"""
import json, glob, sys
from collections import defaultdict
from pathlib import Path

MARKERS = ['[题干 OCR 抽取失败-D11]', '[选项 OCR 抽取失败-D11]', '[题干/选项 OCR 抽取失败-D11]']

def is_bad(q):
    content = q.get('content','') or ''
    if any(m in content for m in MARKERS): return True
    for o in q.get('options',[]) or []:
        c = (o.get('content','') or '') if isinstance(o, dict) else str(o)
        if any(m in c for m in MARKERS): return True
    return False

module = sys.argv[1] if len(sys.argv) > 1 else 'yanyu'
files_bad = defaultdict(list)
for fp in glob.glob(f'src/data/xingce/{module}/*.json'):
    fn = Path(fp).name
    lib = json.load(open(fp, encoding='utf-8'))
    bad = [q['id'].rsplit('-',1)[-1] for q in lib if is_bad(q)]
    if bad:
        files_bad[fn] = bad

total = sum(len(v) for v in files_bad.values())
print(f'[{module}] 缺题文件 {len(files_bad)} 个 / 共 {total} 题')
for fn, qns in sorted(files_bad.items(), key=lambda x: -len(x[1])):
    print(f'  {len(qns):>2}  {fn}  qns={qns}')
