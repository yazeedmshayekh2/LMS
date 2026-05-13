from __future__ import annotations

import re

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from pipeline.ingestion.normalize.llm import _strip_code_fence
from pipeline.ingestion.normalize.readable_prompts import (
    build_readable_system_prompt,
    build_readable_user_prompt,
)

_BATCH_ID_RE = re.compile(r"^p(\d+)_(\d+)$")


def parse_batch_id(batch_id: str) -> tuple[int, int]:
    match = _BATCH_ID_RE.match(batch_id)
    if not match:
        raise ValueError(f"Unsupported section id: {batch_id}")
    return int(match.group(1)), int(match.group(2))


def postprocess_readable_markdown(
    llm: BaseChatModel,
    *,
    page_start: int,
    page_end: int,
    page_types: list[str],
    outline_context: str,
    markdown: str,
) -> str:
    response = llm.invoke(
        [
            SystemMessage(content=build_readable_system_prompt()),
            HumanMessage(
                content=build_readable_user_prompt(
                    page_start=page_start,
                    page_end=page_end,
                    page_types=page_types,
                    outline_context=outline_context,
                    markdown=markdown,
                )
            ),
        ]
    )
    content = getattr(response, "content", response)
    if isinstance(content, list):
        text_parts = [part.get("text", "") for part in content if isinstance(part, dict)]
        content = "\n".join(text_parts)
    return _strip_code_fence(str(content))
