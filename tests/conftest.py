from __future__ import annotations

import sys
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


@pytest.fixture
def sample_chunks():
    from pipeline.ingestion.retrieval.models import RetrievalChunk

    return [
        RetrievalChunk(
            chunk_id="genetics-overview",
            text="تحتوي خلايا الكائنات الحية على المادة الوراثية التي تحدد صفاتها.",
            metadata={"page_start": 8, "unit_title": "الوراثة والتكاثر", "content_kind": "learning_outcomes"},
        ),
        RetrievalChunk(
            chunk_id="reproduction-lesson",
            text="تتكاثر الكائنات الحية بطرائق مختلفة جنسيا ولا جنسيا لتنتج أفرادا جددا.",
            metadata={"page_start": 8, "unit_title": "الوراثة والتكاثر", "content_kind": "learning_outcomes"},
        ),
        RetrievalChunk(
            chunk_id="family-photo-inquiry",
            text="يشترك بعض أفراد العائلة في صفات معينة ويختلفون في صفات أخرى.",
            metadata={"page_start": 8, "unit_title": "الوراثة والتكاثر", "content_kind": "inquiry"},
        ),
    ]
