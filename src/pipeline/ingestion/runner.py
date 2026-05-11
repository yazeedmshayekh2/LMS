from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from pipeline.ingestion.config import IngestionConfig
from pipeline.ingestion.extract.pipeline import run_extraction
from pipeline.ingestion.normalize.pipeline import run_normalization
from pipeline.ingestion.normalize.reader_export import (
    export_readable_document,
    export_readable_sections,
)
from pipeline.ingestion.preprocess.pipeline import run_preprocessing

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class PipelineContext:
    config: IngestionConfig
    provider: str = "gemini"
    model: str | None = None
    dry_run: bool = False


@dataclass(slots=True)
class StageResult:
    stage: str
    artifacts: list[Path] = field(default_factory=list)
    summary: str = ""


@dataclass(frozen=True, slots=True)
class PipelineStage:
    name: str
    description: str
    run: Callable[[PipelineContext], StageResult]


def _stage_preprocess(context: PipelineContext) -> StageResult:
    report = run_preprocessing(context.config)
    artifacts = [
        context.config.preprocess_report_path,
        context.config.output_dir / "preprocess_summary.md",
        context.config.pages_dir,
        context.config.backends_dir,
    ]
    if report.docling_markdown_path:
        artifacts.append(Path(report.docling_markdown_path))
    return StageResult(
        stage="preprocess",
        artifacts=artifacts,
        summary=f"preprocessed {report.processed_pages} page(s)",
    )


def _stage_extract(context: PipelineContext) -> StageResult:
    report = run_extraction(context.config)
    artifacts = [
        Path(report.document_markdown_path),
        context.config.raw_markdown_pages_dir,
        context.config.extract_report_path,
    ]
    return StageResult(
        stage="extract",
        artifacts=artifacts,
        summary=f"extracted {report.processed_pages} page(s)",
    )


def _stage_normalize(context: PipelineContext) -> StageResult:
    report = run_normalization(
        context.config,
        provider_name=context.provider,
        model=context.model,
        dry_run=context.dry_run,
    )
    artifacts = [
        Path(report.document_markdown_path),
        context.config.normalized_sections_dir,
        Path(report.qc_report_path),
        context.config.normalized_markdown_dir / "normalize_report.json",
    ]
    return StageResult(
        stage="normalize",
        artifacts=artifacts,
        summary=f"normalized {report.processed_pages} page(s)",
    )


def _stage_readable(context: PipelineContext) -> StageResult:
    sections_dir = context.config.normalized_sections_dir
    if not sections_dir.is_dir():
        raise FileNotFoundError(
            f"Normalized sections not found: {sections_dir}. Run the normalize stage first."
        )
    readable_sections_dir = context.config.normalized_markdown_dir / "readable" / "sections"
    written = export_readable_sections(sections_dir, output_dir=readable_sections_dir)
    document_path = export_readable_document(
        sections_dir,
        output_path=context.config.normalized_markdown_dir / "readable" / "document.md",
    )
    return StageResult(
        stage="readable",
        artifacts=[document_path, *written],
        summary=f"exported {len(written)} readable section file(s)",
    )


PIPELINE_STAGES: tuple[PipelineStage, ...] = (
    PipelineStage(
        name="preprocess",
        description="Profile pages and compare text-layer backends.",
        run=_stage_preprocess,
    ),
    PipelineStage(
        name="extract",
        description="Hybrid extraction to raw Markdown.",
        run=_stage_extract,
    ),
    PipelineStage(
        name="normalize",
        description="Schema-first LLM normalization with QC.",
        run=_stage_normalize,
    ),
    PipelineStage(
        name="readable",
        description="Export body-only Markdown without chunk frontmatter.",
        run=_stage_readable,
    ),
)

_STAGE_INDEX = {stage.name: index for index, stage in enumerate(PIPELINE_STAGES)}


def stage_names() -> list[str]:
    return [stage.name for stage in PIPELINE_STAGES]


def select_stages(
    *,
    from_stage: str | None = None,
    to_stage: str | None = None,
    only: Sequence[str] | None = None,
) -> list[PipelineStage]:
    if only:
        unknown = [name for name in only if name not in _STAGE_INDEX]
        if unknown:
            raise ValueError(f"Unknown stage(s): {', '.join(unknown)}")
        return [PIPELINE_STAGES[_STAGE_INDEX[name]] for name in only]

    start = _STAGE_INDEX[from_stage or PIPELINE_STAGES[0].name]
    end = _STAGE_INDEX[to_stage or PIPELINE_STAGES[-1].name]
    if start > end:
        raise ValueError("from-stage must come before or equal to to-stage.")
    return list(PIPELINE_STAGES[start : end + 1])


def run_pipeline(
    context: PipelineContext,
    *,
    from_stage: str | None = None,
    to_stage: str | None = None,
    only: Sequence[str] | None = None,
) -> list[StageResult]:
    stages = select_stages(from_stage=from_stage, to_stage=to_stage, only=only)
    results: list[StageResult] = []
    for stage in stages:
        logger.info("Running stage: %s", stage.name)
        result = stage.run(context)
        results.append(result)
        logger.info("Finished stage %s (%s)", stage.name, result.summary)
    return results
