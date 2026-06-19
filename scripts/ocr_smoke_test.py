#!/usr/bin/env python3
"""rapidocr 烟雾测试：跑 2021_fushengjia 答案 PDF 第 5 页，看能否识别中文 + 答案字母。"""
from __future__ import annotations
import sys
import time
from pathlib import Path

import fitz
import numpy as np
from PIL import Image
import io

ROOT = Path(__file__).resolve().parent.parent

PDF = (
    ROOT
    / "material"
    / "【国考】2000-2025真题pdf"
    / "2000-2025国考行测PDF"
    / "行测-答案及解析"
    / "2021年国家公务员考试《行测》真题（副省级）参考答案及解析.pdf"
)

print(f"PDF exists: {PDF.exists()}, size={PDF.stat().st_size if PDF.exists() else 0}")

if not PDF.exists():
    # 用 glob fallback
    import glob
    matches = glob.glob("material/**/2021*副省*答案*.pdf", recursive=True)
    print(f"glob matches: {matches}")
    if matches:
        PDF = Path(matches[0])
        print(f"using: {PDF}")
    else:
        sys.exit(1)

print("\n=== 1. PyMuPDF 渲染第 5 页 ===")
doc = fitz.open(PDF)
print(f"页数: {doc.page_count}")
# 选第 5 页（index 4），已知扫描页
page_idx = 4
page = doc[page_idx]
text_layer = page.get_text()
print(f"  page {page_idx + 1} 文字层字符数: {len(text_layer)}")

# 2x 缩放渲染（300 DPI 等效）
mat = fitz.Matrix(2.0, 2.0)
pix = page.get_pixmap(matrix=mat)
print(f"  渲染图片: {pix.width}x{pix.height}, {pix.colorspace}")

img = Image.open(io.BytesIO(pix.tobytes("png")))
img_np = np.array(img)
print(f"  numpy shape: {img_np.shape}")

print("\n=== 2. RapidOCR 初始化（GPU 模式，首次会下模型）===")
t0 = time.time()
sys.path.insert(0, str(ROOT / "scripts"))
from ocr_engine import make_engine  # type: ignore[import-not-found]

engine = make_engine()
print(f"  初始化耗时: {time.time() - t0:.1f}s")

print("\n=== 3. 识别（GPU）===")
# 先 warm up（首次 CUDA kernel 编译会偏慢，第二次才是稳定速度）
_ = engine(img_np)
t0 = time.time()
result = engine(img_np)
print(f"  OCR 耗时: {time.time() - t0:.2f}s（已 warm up）")
print(f"  结果类型: {type(result).__name__}")

# rapidocr 3.x 返回 RapidOCROutput 对象
# 兼容多种返回格式
texts = []
if hasattr(result, "txts") and result.txts is not None:
    texts = list(result.txts)
elif hasattr(result, "text") and result.text is not None:
    texts = list(result.text)
elif isinstance(result, tuple) and len(result) >= 2:
    # 老 API: (boxes, text)
    if result[1] is not None:
        for item in result[1]:
            if isinstance(item, (list, tuple)) and len(item) >= 1:
                texts.append(item[0])
            else:
                texts.append(str(item))

print(f"  识别行数: {len(texts)}")
print("\n=== 4. 前 30 行识别文字 ===")
for i, t in enumerate(texts[:30]):
    print(f"  [{i:>2}] {t}")

# 找答案模式
print("\n=== 5. 寻找答案标志 ===")
joined = "\n".join(texts)
import re
ans_matches = re.findall(r"故正确答案为\s*([A-D]+)", joined)
print(f"  '故正确答案为' 出现次数: {len(ans_matches)}, 答案: {ans_matches}")

# 保存识别全文供查看
out_txt = ROOT / "archive" / "reports" / f"ocr_smoke_2021fsj_p{page_idx + 1}.txt"
out_txt.parent.mkdir(parents=True, exist_ok=True)
out_txt.write_text(joined, encoding="utf-8")
print(f"  全文落: {out_txt}")
