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
