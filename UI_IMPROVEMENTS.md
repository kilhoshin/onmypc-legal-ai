# UI and Search Enhancements

## Delivered Improvements

### 1. Rich search result presentation

**Before**
```
Document 1: sample_contract.txt
Page 2
Score: 85.3%
```

**After**
```
employment_agreement_ny.txt • Page 2, §Article IV
ARTICLE I > EMPLOYMENT AND DUTIES > §4.2 Non-Compete
[CONTRACT] [NY] Score: 85.3%

Debug (dev only):
BM25: 3.604 | Vector: 0.541 | Final: 0.017
```

Changes include:
- Display the human-readable filename.
- Show page range and section title.
- Render a breadcrumb for the section hierarchy.
- Add document type and jurisdiction badges.
- Highlight only the text that matched the query.
- Surface the scoring breakdown (BM25, vector, final) while in development mode.

### 2. Smart result filtering

Hybrid selection logic keeps the list concise but useful:

```python
score_threshold = 0.01  # minimum relevance
min_results = 3         # guarantee enough hits
max_results = 10        # avoid overwhelming the user
```

Rules applied:
1. If enough results exceed the threshold → show only those (up to `max_results`).
2. If too few pass the threshold → include the best low-score results until `min_results` is satisfied.
3. Never exceed `max_results`.

### 3. Automatic knowledge-base management

Workflow:
1. On startup the app attempts to load existing indexes.
2. Indexed files are tracked via file hashes to avoid reprocessing unchanged documents.
3. Only new or modified files are parsed on each indexing run.
4. A "Re-index" action forces a full rebuild when desired.

Stored artifacts:
```
data/
├─ structured_documents.json   # metadata
├─ enriched_chunks.json        # chunks + embeddings
├─ faiss_index.bin             # FAISS vectors
└─ bm25/bm25_corpus.json       # BM25 corpus
```

---

## Visual Refinements

- **Document type badges**: CONTRACT (blue), NDA (purple), POLICY (green), LICENSE (orange), etc.
- **Jurisdiction badges**: CA (purple), NY (blue), TX (red), etc.
- **Score indicator**: green text when confidence is high.
- **Highlights**: yellow gutter bar alongside matching sentences.

Example render:
```
=============================================================
employment_agreement_ny.txt • Pages 2-3, §4.2 Non-Compete
-------------------------------------------------------------
[CONTRACT] [NY] Score: 91.2%

ARTICLE IV > RESTRICTIVE COVENANTS > 4.2 Non-Compete

Employee acknowledges that New York law permits reasonable
non-compete agreements. Employee agrees not to work for any
direct competitor in the software development industry within
50 miles of New York City for 12 months following termination...

Debug: BM25: 3.604 | Vector: 0.541 | Final: 0.912
=============================================================
```

---

## Tunable Parameters

`backend/services/hybrid_search.py`
```python
score_threshold = 0.01
min_results = 3
max_results = 10

bm25_weight = 0.4
vector_weight = 0.6

boost_factors = {
    "is_header": 1.3,
    "is_definition": 1.2,
    "signed_doc": 1.3,
    "recent_doc": 1.2,
}
```

`backend/services/query_agent.py`
```python
# Response assembly defaults
temperature = 0.3
num_predict = 512
```

---

## UX Impact

**Before**
```
Document 1
Document 2
Document 3
```

**After**
```
employment_agreement_ny.txt (Page 2, §4.2)
└─ ARTICLE IV > RESTRICTIVE COVENANTS
   [CONTRACT] [NY] Score: 91%

sample_contract.txt (Page 1)
└─ TERMS AND CONDITIONS > 2. NON-COMPETE
   [CONTRACT] [CA] Score: 87%
```

Users now see context, document types, and confidence at a glance.

---

## Next Ideas

1. **File watcher** – automatically trigger incremental reindexing when new documents land in the watched folder.
2. **Saved searches** – persist frequently used queries for quick access.
3. **Result pinning** – allow users to pin key findings to a session summary.
