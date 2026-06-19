"""D-13 审计：找出 cross-module 误打到 changshi 的题（实际是资料分析等其他模块）"""
import json, glob
from pathlib import Path

KP_KEYWORDS = {
    "changshi": ["饼图", "下列说法", "宪法", "党章", "习近平", "二十大", "刑法", "民法典",
                 "下列哪", "属于", "法律", "条例", "中国", "下列正确"],
    "ziliao": ["%", "增长率", "占比", "比 上 年", "比 上 月", "图中显示", "下表",
               "数据显示", "增长", "下降", "总收入", "亿元", "万元"],
}

problematic = []
for fp in glob.glob("src/data/xingce/changshi/*.json"):
    lib = json.load(open(fp, encoding="utf-8"))
    fn = Path(fp).name
    for q in lib:
        exp = q.get("explanation", "") or ""
        if "D13 救援" not in exp:
            continue
        opts = q.get("options", []) or []
        # 检查图片选项（< 5% 常识题应有图）
        has_img = any('<img' in (o.get("content","") or "") for o in opts if isinstance(o, dict))
        # 检查内容关键词倾向
        content = q.get("content", "") or ""
        if has_img and "饼图" in content or "占比" in content or "增长率" in content:
            problematic.append((fn, q["id"][-3:], "资料分析题图(误打入 changshi)"))
            continue
        if has_img:
            problematic.append((fn, q["id"][-3:], "选项含图(可疑非常识)"))
            continue
        # 跨模块标记
        if "fallback_xmod" in exp:
            problematic.append((fn, q["id"][-3:], "cross-module 救援"))

for fn, qid, reason in problematic:
    print(f"  {fn}  qn={qid}  {reason}")
print(f"\n共 {len(problematic)} 题可疑")
