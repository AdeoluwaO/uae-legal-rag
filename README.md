# UAE Legal RAG System

A precision-oriented question-answering system over UAE legal documents with article-level citations.

## Overview

This system ingests a corpus of UAE legal documents (federal laws, executive regulations, DIFC laws) and answers user questions with:
- Grounded answers citing specific articles
- Authoritative document selection (jurisdiction, version, instrument hierarchy aware)
- Refusal on ambiguous or out-of-corpus questions
- Detailed tracing of retrieval and generation logic


## Installation

### Prerequisites
- Python 3.9+
- ~2GB disk space (for embedding model)

### Setup

```bash
# Clone repo
git clone <repo-url>
cd uae-legal-rag

# Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

```

## Quick Start

### 1. Ingest the Corpus

Extract and index all PDF documents from the manifest:

```bash
python3 main.py
```

**Output:**
- `generated_data/articles_index.json` — Indexed articles with embeddings (13 MB)
- `eval/results/indexing.json` — Ingestion status and statistics
- Logs showing per-document status

### 2. Ask a Question

```bash
python3 main.py ask "What is the notice period for terminating employment onshore UAE?"
```

**Output:**
- Answer with citations
- Result saved to `eval/results/answer_TIMESTAMP.json`

### 3. Run Evaluation

Test against golden set:

```bash
python3 run_eval.py
```

## Commands Reference

### Ingest Corpus
```bash
python3 main.py
```
Parses all PDFs in `input_corpus/data/`, extracts articles, embeds them, and saves index.

### Ask Question
```bash
python3 main.py ask "<your question here>"
```
Retrieves relevant articles and generates answer with citations.

### Run Tests
```bash
python3 -m pytest tests/ -v
```


## Evaluation Metrics

Metrics are calculated from a golden set of 16 test cases covering:
- Version-ambiguous queries (repealed laws)
- Jurisdiction-ambiguous queries (federal vs DIFC)
- Instrument hierarchy (base law vs exec regulation)
- Factual article lookups
- Refusal cases (legal advice, out-of-corpus)

See `eval/golden_set.jsonl` for full set.

## Project Structure

```
├── src/
│   ├── core/              # Types, manifest loading
│   ├── ingestion/         # PDF parsing, chunking
│   ├── storage/           # Article storage, vector search
│   ├── retrieval/         # Document selection, routing
│   ├── generation/        # Answer generation, grounding
│   └── evaluation/        # Metrics, evaluation
├── tests/                 # Unit and integration tests
├── eval/                  # Evaluation artifacts
│   ├── golden_set.jsonl   # Test cases
│   └── results/           # Query traces, metrics
├── input_corpus/          # PDFs and manifest
├── requirements.txt       # Python dependencies
├── main.py               # Entry point
└── REPORT.md             # Architectural decisions
```

## Architectural Decisions

See `REPORT.md` for detailed discussion of:
- Document selection logic (jurisdiction, version, instrument)
- Chunking strategy (article-level with paragraph preservation)
- Vector embedding model choice
- Quotation fidelity requirements
- Trade-offs (quality vs latency vs cost)
