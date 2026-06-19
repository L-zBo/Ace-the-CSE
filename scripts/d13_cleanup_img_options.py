"""D-13 清洗：把 src/data/xingce/ 里所有 D-13 救援的 <img src=> 选项就地转 [图形选项]"""
import json, glob
from pathlib import Path

modified = 0
files_changed = []
for fp in glob.glob("src/data/xingce/*/*.json"):
    lib = json.load(open(fp, encoding="utf-8"))
    changed = False
    for q in lib:
        exp = q.get("explanation", "") or ""
        if "D13 救援" not in exp:
            continue
        opts = q.get("options", []) or []
        has_img = any(("<img" in (o.get("content","") or "") if isinstance(o, dict) else "<img" in str(o))
                      or ("upload.gkzhenti" in (o.get("content","") or "") if isinstance(o, dict) else False)
                      for o in opts)
        if not has_img:
            continue
        # 全转 [图形选项]
        q["options"] = [{"label": L, "content": "[图形选项]"} for L in "ABCD"]
        if "[图形选项]" not in exp:
            q["explanation"] = exp + "\n[D-13 后清洗：原 baijing 含 <img>，转 [图形选项]，前端需补 PNG]"
        changed = True
        modified += 1
    if changed:
        Path(fp).write_text(json.dumps(lib, ensure_ascii=False, indent=2), encoding="utf-8")
        files_changed.append(fp)

print(f"[清洗] {modified} 题修复，{len(files_changed)} 文件改动")
for fp in files_changed[:10]:
    print(f"  {fp}")
