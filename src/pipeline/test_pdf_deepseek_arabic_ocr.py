"""OCR the first pages of the sample PDF with Hugging Face Arabic DeepSeek-OCR-2.

Uses `loay/Arabic-OCR-DeepSeek-OCR-2` (see model card:
https://huggingface.co/loay/Arabic-OCR-DeepSeek-OCR-2).

**Requires an NVIDIA GPU with CUDA.** The model's remote `infer()` implementation
hardcodes `.cuda()`; CPU execution is not supported by that code path.

Renders pages with pdf2image (Poppler), runs the VLM per page with the fine-tune's
*Free OCR* style prompt, and writes a UTF-8 report under `assets/`.

Optional: set `HF_TOKEN` in the environment (or `.env` via dotenv) for higher
Hugging Face Hub rate limits.

Run from repo root:
  uv run python src/pipeline/test_pdf_deepseek_arabic_ocr.py
"""

from __future__ import annotations

import logging
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

MAX_PAGES = 10
MODEL_ID = "loay/Arabic-OCR-DeepSeek-OCR-2"
PDF_FILENAME = "علوم ثامن طالب ف1 S .pdf"
OUTPUT_REL = Path("assets") / "pdf_mining_first10_deepseek_arabic_ocr.txt"

# Prompt must contain at least one space for the model's `infer(..., eval_mode=True)`
# return path (see upstream `modeling_deepseekocr2.py`).
FREE_OCR_PROMPT = " \nFree OCR.\n"


def _patch_deepseek_v2_for_hub_ocr_model() -> None:
    """Hub `modeling_deepseekocr2.py` imports `DeepseekV2MoE`; newer transformers expose `DeepseekV2Moe`."""
    import transformers.models.deepseek_v2.modeling_deepseek_v2 as ds

    if hasattr(ds, "DeepseekV2MoE"):
        return
    moe = getattr(ds, "DeepseekV2Moe", None)
    if moe is None:
        return
    ds.DeepseekV2MoE = moe


# Hub config.json uses `"kv_lora_rank": null` inside `language_config`; `@strict` DeepseekV2Config
# requires `int` (default 512). See transformers DeepseekV2Config.
_STRICT_KV_LORA_DEFAULT = 512


def _fix_strict_deepseek_kv_lora(obj: object) -> None:
    if isinstance(obj, dict):
        if obj.get("kv_lora_rank") is None:
            obj["kv_lora_rank"] = _STRICT_KV_LORA_DEFAULT
        for v in obj.values():
            _fix_strict_deepseek_kv_lora(v)
    elif isinstance(obj, list):
        for item in obj:
            _fix_strict_deepseek_kv_lora(item)


def _load_auto_config_fixed(model_id: str):
    """Load config from the Hub and patch known strict-validation mismatches.

    We cannot rely on ``AutoConfig.from_pretrained`` after editing JSON: remote-code
    config loading re-fetches from the repo and would hit the same ``kv_lora_rank``
    validation error. Resolve the Hub config class and build from a patched dict.
    """
    import json

    from huggingface_hub import hf_hub_download
    from transformers.dynamic_module_utils import (  # type: ignore[import-untyped]
        get_class_from_dynamic_module,
    )

    path = hf_hub_download(repo_id=model_id, filename="config.json")
    with open(path, encoding="utf-8") as f:
        config_dict = json.load(f)
    _fix_strict_deepseek_kv_lora(config_dict)
    class_ref = config_dict["auto_map"]["AutoConfig"]
    config_class = get_class_from_dynamic_module(class_ref, model_id)
    config_class.register_for_auto_class()
    return config_class.from_dict(config_dict)


def _load_dotenv() -> None:
    try:
        from dotenv import find_dotenv, load_dotenv

        load_dotenv(find_dotenv())
    except ImportError:
        pass


def main() -> int:
    _load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(message)s",
        stream=sys.stderr,
        force=True,
    )

    here = Path(__file__).resolve().parent
    pdf_path = here / PDF_FILENAME
    out_path = here / OUTPUT_REL
    out_path.parent.mkdir(parents=True, exist_ok=True)

    header_lines = [
        f"Arabic DeepSeek-OCR-2 — first {MAX_PAGES} pages",
        f"Model: {MODEL_ID}",
        f"Source: {pdf_path}",
        f"Written: {datetime.now(timezone.utc).isoformat()}",
        "",
    ]

    if not pdf_path.is_file():
        msg = f"PDF not found: {pdf_path}"
        logging.error(msg)
        out_path.write_text("\n".join(header_lines + [msg + "\n"]), encoding="utf-8")
        return 1

    try:
        import torch
    except ImportError as e:
        msg = f"torch not available: {e}"
        logging.error(msg)
        out_path.write_text("\n".join(header_lines + [msg + "\n"]), encoding="utf-8")
        return 1

    if not torch.cuda.is_available():
        msg = (
            "CUDA is not available. This checkpoint's `infer()` uses `.cuda()` only; "
            "run on a machine with an NVIDIA GPU and CUDA-enabled PyTorch."
        )
        logging.error(msg)
        out_path.write_text("\n".join(header_lines + [msg + "\n"]), encoding="utf-8")
        return 1

    from pdf2image import convert_from_path

    _patch_deepseek_v2_for_hub_ocr_model()
    from transformers import AutoModel, AutoTokenizer  # type: ignore[import-untyped]

    logging.info("Rasterizing PDF (first %s pages)…", MAX_PAGES)
    images = convert_from_path(
        str(pdf_path),
        first_page=1,
        last_page=MAX_PAGES,
        dpi=200,
    )

    logging.info("Loading tokenizer and model from Hugging Face (may download)…")
    config = _load_auto_config_fixed(MODEL_ID)
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_ID,
        trust_remote_code=True,
        config=config,
    )

    dtype = torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    model = None
    last_err: Exception | None = None
    for attn in ("flash_attention_2", "sdpa", "eager"):
        try:
            model = AutoModel.from_pretrained(
                MODEL_ID,
                trust_remote_code=True,
                config=config,
                torch_dtype=dtype,
                attn_implementation=attn,
            )
            logging.info("Loaded model with attn_implementation=%s", attn)
            break
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            logging.warning("Load with %s failed: %s", attn, exc)
    if model is None:
        msg = f"Could not load model: {last_err!r}"
        logging.error(msg)
        out_path.write_text("\n".join(header_lines + [msg + "\n"]), encoding="utf-8")
        return 1

    model = model.eval().cuda()

    body: list[str] = [
        "=" * 72,
        "Per-page OCR (infer, eval_mode=True, Free OCR prompt)",
        "=" * 72,
        "",
    ]

    with tempfile.TemporaryDirectory(prefix="deepseek_ar_ocr_") as tmpdir:
        tmp = Path(tmpdir)
        for i, pil in enumerate(images, start=1):
            img_path = tmp / f"page_{i:03d}.png"
            pil.save(img_path, format="PNG")
            logging.info("Page %s/%s — running infer…", i, len(images))
            page_out = model.infer(
                tokenizer,
                prompt=FREE_OCR_PROMPT,
                image_file=str(img_path),
                output_path=str(tmp / f"out_{i:03d}"),
                base_size=1024,
                image_size=768,
                crop_mode=True,
                save_results=False,
                eval_mode=True,
            )
            body.append(f"--- Page {i} ---\n")
            body.append((page_out or "").strip() or "(empty model output)")
            body.append("")

    text = "\n".join(header_lines + body) + "\n"
    out_path.write_text(text, encoding="utf-8")
    logging.info("Wrote %s (%s bytes)", out_path, out_path.stat().st_size)
    print(f"Wrote {out_path} ({out_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
