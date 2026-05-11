from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline.ingestion.models import (
    BackendExtraction,
    LayoutSignals,
    PageGeometry,
    PageProfile,
    PageType,
    PreprocessReport,
    TextSignals,
)


def _text_signals(data: dict[str, Any] | None) -> TextSignals | None:
    if data is None:
        return None
    return TextSignals(**data)


def _page_profile(data: dict[str, Any]) -> PageProfile:
    geometry = PageGeometry(**data["geometry"])
    layout = LayoutSignals(**data["layout"])
    backends = [
        BackendExtraction(
            backend=item["backend"],
            ok=item["ok"],
            char_count=item["char_count"],
            text_signals=_text_signals(item.get("text_signals")),
            text=item.get("text", item.get("preview", "")),
            quality_score=item["quality_score"],
            error=item.get("error"),
            extra=item.get("extra", {}),
        )
        for item in data["backends"]
    ]
    return PageProfile(
        page_number=data["page_number"],
        page_type=PageType(data["page_type"]),
        classification_confidence=data["classification_confidence"],
        classification_reasons=data["classification_reasons"],
        geometry=geometry,
        layout=layout,
        primary_text_signals=TextSignals(**data["primary_text_signals"]),
        backends=backends,
        recommended_backends=data["recommended_backends"],
        flags=data.get("flags", []),
    )


def load_preprocess_report(path: Path) -> PreprocessReport:
    payload = json.loads(path.read_text(encoding="utf-8"))
    pages = [_page_profile(item) for item in payload["pages"]]
    return PreprocessReport(
        source_pdf=payload["source_pdf"],
        written_at=payload["written_at"],
        page_count=payload["page_count"],
        processed_pages=payload["processed_pages"],
        document_metadata=payload["document_metadata"],
        backend_summary=payload["backend_summary"],
        pages=pages,
        docling_markdown_path=payload.get("docling_markdown_path"),
        notes=payload.get("notes", []),
    )
