"""D-16 L-7a 扫占位题对应 PNG 文件存在性（含 questionImage 字段补齐 dry-run/apply）"""
import argparse
import glob
import json
import re
from pathlib import Path

MARKERS = ['[选项 OCR 抽取失败-D11]', '[暂缺]', '[题干 OCR 抽取失败-D11]', '[题干/选项 OCR 抽取失败-D11]']
DERIVED = ['[由解析推导-D16L2]', '[由aipta救援-D16L3]', '[由WebSearch救援-D16L6]']


def is_bad_opt(s):
    if not s: return True
    s = s.strip()
    if not s or s in ('缺失', '暂缺'): return True
    if any(d in s for d in DERIVED): return False
    return any(m in s for m in MARKERS)


def is_placeholder(q):
    c = q.get('content', '') or ''
    if any(m in c for m in MARKERS): return True
    opts = q.get('options', []) or []
    bad = sum(1 for o in opts if is_bad_opt(
        (o.get('content', '') or '') if isinstance(o, dict) else str(o)))
    return bad >= 2


def qid_to_examkey(qid: str) -> str:
    """从 qid 推 PNG 目录约定的 examKey"""
    parts = qid.split('-')
    if not parts: return ''
    src = parts[0]
    if src == 'national':
        # national-xingce-panduan-2024-dishi-071
        # examKey = national_2024_dishi
        if len(parts) >= 6:
            return f'national_{parts[3]}_{parts[4]}'
    elif src == 'provincial':
        # provincial-shanghai-xingce-changshi-2023-049
        # examKey = provincial_shanghai_2023
        if len(parts) >= 6:
            return f'provincial_{parts[1]}_{parts[4]}'
    return ''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--apply', action='store_true')
    args = ap.parse_args()

    fixable = []  # (fp, qid, png_path)
    pkg_dir = Path('public/img/questions')
    for mod in ['panduan', 'changshi', 'shuliang', 'ziliao', 'yanyu']:
        for fp in sorted(glob.glob(f'src/data/xingce/{mod}/*.json')):
            lib = json.loads(Path(fp).read_text(encoding='utf-8'))
            dirty = False
            for q in lib:
                if not is_placeholder(q): continue
                if q.get('questionImage'): continue  # 已有，不动
                qid = q.get('id', '')
                qn_str = qid.rsplit('-', 1)[-1]
                try: qn_int = int(qn_str)
                except: continue
                ek = qid_to_examkey(qid)
                if not ek: continue
                # 尝试 q{NN}.png / q{NNN}.png
                for fmt in ('02d', '03d'):
                    png = pkg_dir / ek / f'q{qn_int:{fmt}}.png'
                    if png.exists():
                        fixable.append((fp, qid, f'/img/questions/{ek}/{png.name}'))
                        if args.apply:
                            q['questionImage'] = f'/img/questions/{ek}/{png.name}'
                            dirty = True
                        break
            if dirty and args.apply:
                Path(fp).write_text(
                    json.dumps(lib, ensure_ascii=False, indent=2),
                    encoding='utf-8',
                )

    print(f'[{"APPLY" if args.apply else "DRY-RUN"}] 可补 questionImage: {len(fixable)} 题')
    for fp, qid, png in fixable[:30]:
        print(f'  {qid} -> {png}')
    if len(fixable) > 30:
        print(f'  ...还有 {len(fixable) - 30} 题')


if __name__ == '__main__':
    main()
