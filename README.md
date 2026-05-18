# 📚 LMS — Learning Management System

A modern Learning Management System built with AI-powered features for an enhanced learning experience.

## 🚀 Features

- User authentication and role-based access control (Admin, Instructor, Student)
- Course creation and management
- AI-assisted content recommendations
- Progress tracking and analytics dashboard
- Assignment submission and grading system
- RESTful API backend

## 🛠️ Tech Stack

| Layer       | Technology           |
| ----------- | -------------------- |
| Backend     | FastAPI (Python)     |
| Frontend    | React.js / Next.js   |
| Database    | PostgreSQL           |
| Auth        | Azure AD / JWT       |
| AI Features | OpenAI / HuggingFace |
| Deployment  | Docker, Azure / GCP  |

## 📦 Installation

### Prerequisites

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) (recommended for the Python pipeline)
- Node.js 18+ (frontend)
- PostgreSQL (application backend)
- Docker (optional)
- Poppler (`pdftoppm` / `pdftotext`) for PDF page rendering and text extraction

### Backend Setup

```bash
git clone https://github.com/yazeedmshayekh2/LMS.git
cd LMS
uv sync
```

You can also use a virtual environment and install from `pyproject.toml` if you prefer not to use `uv`.

### Environment Variables

Create a `.env` file in the repo root. Start from `.env.example` and add the keys you need.

```env
DATABASE_URL=postgresql://user:password@localhost:5432/lms_db
SECRET_KEY=your_secret_key
OPENAI_API_KEY=your_openai_api_key
GOOGLE_API_KEY=your_gemini_api_key
AZURE_CLIENT_ID=your_azure_client_id
```

`GOOGLE_API_KEY` is used by stage 3 normalization when `--provider gemini` is selected. `GEMINI_API_KEY` is also accepted.

### Run the Application

```bash
# Backend
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## 🐳 Docker

```bash
docker-compose up --build
```

## 📁 Project Structure

```
LMS/
├── src/
│   ├── pipeline/                 # Textbook PDF ingestion CLI and stages
│   │   ├── run_pipeline.py       # Run the full pipeline
│   │   ├── run_preprocess.py
│   │   ├── run_extract.py
│   │   ├── run_normalize.py
│   │   ├── run_export_readable.py
│   │   ├── run_test_retrieval.py # Hybrid retrieval smoke test (BM25 + embeddings)
│   │   └── ingestion/            # Stage implementations and orchestrator
│   │       └── retrieval/        # Chunk loading, embeddings, hybrid search
│   ├── agents/
│   └── ai/
├── frontend/
├── pyproject.toml
└── README.md
```

Generated pipeline artifacts are written under `src/pipeline/assets/` and are ignored by git.

## Textbook PDF ingestion

The ingestion flow turns a textbook PDF into structured Markdown for later LMS and RAG work. The default sample book lives in `src/pipeline/`.

### Pipeline stages

| Stage        | Purpose                                                        | Main outputs                               |
| ------------ | -------------------------------------------------------------- | ------------------------------------------ |
| `preprocess` | Profile pages, compare text-layer backends, classify page type | `src/pipeline/assets/preprocess/`          |
| `extract`    | Hybrid text-layer extraction to raw Markdown                   | `src/pipeline/assets/raw_markdown/`        |
| `normalize`  | Schema-first LLM cleanup and chunk metadata                    | `src/pipeline/assets/normalized/`          |
| `readable`   | Body-only Markdown without per-chunk YAML frontmatter          | `src/pipeline/assets/normalized/readable/` |

Stage order is defined in `src/pipeline/ingestion/runner.py` in `PIPELINE_STAGES`.

### Run the full pipeline

From the repo root:

```bash
uv run python src/pipeline/run_pipeline.py --max-pages 10 --skip-docling
```

Useful flags:

- `--all-pages` processes the full PDF instead of `--max-pages`
- `--pdf /path/to/book.pdf` overrides the default sample PDF
- `--skip-docling` skips slow Docling work during preprocessing
- `--with-docling` appends a Docling appendix during extraction
- `--dry-run` writes normalization prompts and placeholders without calling an LLM
- `--list-stages` prints the registered stages

Example with Gemini normalization:

```bash
uv run python src/pipeline/run_pipeline.py \
  --max-pages 10 \
  --skip-docling \
  --provider gemini \
  --model gemini-2.5-flash \
  --batch-size 1
```

### Run part of the pipeline

```bash
uv run python src/pipeline/run_pipeline.py --list-stages
uv run python src/pipeline/run_pipeline.py --from-stage extract --to-stage normalize
uv run python src/pipeline/run_pipeline.py --only readable
```

Each stage can also be run on its own:

```bash
uv run python src/pipeline/run_preprocess.py --skip-docling --max-pages 10
uv run python src/pipeline/run_extract.py --max-pages 10
uv run python src/pipeline/run_normalize.py --provider gemini --batch-size 1
uv run python src/pipeline/run_export_readable.py
```

### Where to read results

- Preprocess summary: `src/pipeline/assets/preprocess/preprocess_summary.md`
- Raw page Markdown: `src/pipeline/assets/raw_markdown/pages/page_###.md`
- Normalized chunks with metadata: `src/pipeline/assets/normalized/sections/p###_###.md`
- Human-readable export: `src/pipeline/assets/normalized/readable/document.md`
- Normalization QC: `src/pipeline/assets/normalized/qc_report.json`

The readable export removes the YAML frontmatter blocks used for chunking. The normalized section files keep that metadata for downstream ingestion.

### Hybrid retrieval (RAG smoke test)

After normalization, you can search normalized chunks with **hybrid retrieval**: BM25 (sparse) plus dense embeddings (cosine similarity), fused with reciprocal rank fusion (RRF).

Implementation lives in `src/pipeline/ingestion/retrieval/`. Chunks are loaded from `src/pipeline/assets/normalized/sections/p###_###.md` (YAML frontmatter + body per chunk).

| Score (CLI) | Meaning |
| ----------- | ------- |
| `rrf` | Fusion score from ranks (small values, e.g. 0.01–0.03, are normal) |
| `cosine` | Dense similarity between query and chunk embeddings (often ~0.5–0.95) |
| `bm25` | Sparse lexical score (scale depends on corpus size) |

**Offline / CI** (no API keys; uses deterministic fake embeddings):

```bash
uv run python src/pipeline/run_test_retrieval.py --embedding-provider fake
uv run pytest tests/test_retrieval.py -v
```

**Semantic search with Gemini** (set `GOOGLE_API_KEY` or `GEMINI_API_KEY` in `.env`):

```bash
uv run python src/pipeline/run_test_retrieval.py \
  --embedding-provider gemini \
  --query "المادة الوراثية" \
  --top-k 5
```

**OpenAI embeddings:**

```bash
uv run python src/pipeline/run_test_retrieval.py \
  --embedding-provider openai \
  --embedding-model text-embedding-3-small \
  --query "كيف تتكاثر الكائنات الحية؟"
```

Useful flags:

- `--sections-dir` — override normalized sections directory
- `--query` — repeat for multiple queries (defaults to sample Arabic queries)
- `--json` — machine-readable output with `rrf_score`, `bm25_score`, `cosine_score`
- `--embedding-model` — override provider default (Gemini default: `models/gemini-embedding-001`)

Embedding providers: `gemini`, `openai` / `gpt`, `ollama`, `fake`.

### LLM providers for normalization

Stage 3 supports `gemini`, `gpt`, `claude`, `groq`, and `ollama` through `src/ai/llms/factory.py`.

- Gemini: set `GOOGLE_API_KEY` in `.env`
- OpenAI: set `OPENAI_API_KEY`
- Ollama local example:

```bash
uv run python src/pipeline/run_pipeline.py \
  --only normalize \
  --provider ollama \
  --model qwen2.5:14b-instruct-q4_K_M \
  --batch-size 1
```

If no provider credentials are available, normalization falls back to dry-run behavior unless you pass `--dry-run` explicitly.

### Add a new stage

1. Implement the stage logic under `src/pipeline/ingestion/`.
2. Add a runner function that returns `StageResult`.
3. Register a new `PipelineStage` in `PIPELINE_STAGES` inside `src/pipeline/ingestion/runner.py`.

The orchestrator in `src/pipeline/run_pipeline.py` will pick up the new stage automatically for `--list-stages`, `--from-stage`, `--to-stage`, and `--only`.

### Legacy benchmark scripts

`src/pipeline/test_pdf_mining_first10.py` and `src/pipeline/test_pdf_deepseek_arabic_ocr.py` are standalone experiments for comparing extractors and GPU OCR. They are not part of the main `run_pipeline.py` flow.

## 🧪 Testing

```bash
uv run pytest tests/ -v
```

Retrieval tests use fake embeddings by default; `test_load_chunks_from_real_sections` runs when normalized section assets exist locally.

## 📄 API Documentation

Once running, visit:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add your feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Yazeed Mshayekh**  
AI Engineer | Full-Stack Developer  
[GitHub](https://github.com/yazeedmshayekh2)
