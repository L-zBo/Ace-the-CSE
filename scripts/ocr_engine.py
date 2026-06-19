"""统一的 RapidOCR 引擎工厂：默认启用 CUDA GPU，CPU 兜底。

用法：
    from ocr_engine import make_engine
    engine = make_engine()                  # GPU（onnxruntime-gpu CUDAExecutionProvider）
    engine = make_engine(use_gpu=False)     # 强制 CPU

要求：onnxruntime-gpu 已安装且 CUDAExecutionProvider 在 get_available_providers() 中。
若 CUDA EP 不可用，自动回落 CPU 并打印告警。
"""
from __future__ import annotations

import sys

from rapidocr import RapidOCR  # type: ignore[import-not-found]


def _cuda_available() -> bool:
    try:
        import onnxruntime as ort  # type: ignore[import-not-found]
        return "CUDAExecutionProvider" in ort.get_available_providers()
    except Exception:
        return False


def make_engine(use_gpu: bool = True, device_id: int = 0) -> RapidOCR:
    """构建 RapidOCR 引擎。默认 GPU。"""
    if use_gpu and _cuda_available():
        print(f"[ocr_engine] CUDA GPU device={device_id} 启用", file=sys.stderr, flush=True)
        return RapidOCR(params={
            "EngineConfig.onnxruntime.use_cuda": True,
            "EngineConfig.onnxruntime.cuda_ep_cfg.device_id": device_id,
        })
    if use_gpu:
        print("[ocr_engine] WARN: CUDAExecutionProvider 不可用，回落 CPU。检查 onnxruntime-gpu 是否安装。", file=sys.stderr, flush=True)
    else:
        print("[ocr_engine] CPU 模式", file=sys.stderr, flush=True)
    return RapidOCR()
