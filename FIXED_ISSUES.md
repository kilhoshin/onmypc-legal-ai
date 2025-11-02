# Issues Resolved

## Reported symptoms

1. Search results appeared as “Document 1, Document 2…” instead of real filenames.
2. Users were unsure whether the knowledge base persisted between sessions.

## Root causes

- **Bloated response payloads**: the backend attempted to ship entire documents, all chunks, and embedding vectors in a single JSON response. Browsers could not reliably parse or render that payload.
- **UI feedback**: although the knowledge base was already being auto-loaded, the interface did not communicate that fact.

## Fixes

### Lightweight API models

Created `backend/api/response_models.py` with trimmed Pydantic models:

- `DocumentMetadata` – `doc_id`, `title`, `file_path`, `doctype`, `jurisdiction`, etc.
- `ChunkMetadata` – `chunk_id`, `text`, `section_path`, `page_start/end`.
- `SearchResultResponse` – combines the metadata plus scoring fields.

Added `convert_to_api_response()` to map the internal rich response into the lightweight representation. Embedding vectors and large blobs are no longer serialized.

### `/api/query` response

`backend/api/routes.py` now returns `QueryResponseAPI` and always funnels results through `convert_to_api_response()`. Frontend receives only what it needs.

### Status feedback

`StatusResponse` gained `knowledge_base_loaded: bool`. The React app uses this flag to preselect the folder UI state:

```javascript
const status = await apiService.getStatus();
if (status.knowledge_base_loaded) {
  setFolderSelected(true);
  setSelectedFolder('Auto-loaded from previous session');
}
```

### Result rendering

With the new data shape the renderer can display:
- Actual filename
- Page range and section title
- Section breadcrumb
- Document type and jurisdiction badges
- Relevance score and debug metrics (during development)

Example:
```
=============================================================
software_license_agreement.txt • Page 3, §3.1 License Fee
-------------------------------------------------------------
[LICENSE] [DE] Score: 95.2%

SECTION 3: FEES AND PAYMENT > 3.1 License Fee

- Initial license fee: $500,000 (due upon execution)
- Annual maintenance fee: $150,000 (due each anniversary date)

Debug: BM25: 4.521 | Vector: 0.823 | Final: 0.952
=============================================================
```

## Current behaviour

- **First run**: user accepts the EULA, selects a folder, indexing runs, and documents are stored under `data/`.
- **Subsequent runs**: indexes load automatically, the UI reports “Auto-loaded from previous session”, and search is immediately available.

## Knowledge base storage

```
data/
├─ structured_documents.json
├─ enriched_chunks.json
├─ faiss_index.bin
└─ bm25/bm25_corpus.json
```

Incremental indexing uses file hashes to skip unchanged documents. New files are added and modified files are reprocessed.

## Next steps

- Restart the Electron shell (`npm run dev` from `frontend/`) to verify instant search availability.
- Use “Settings → Re-index Documents” when new material is dropped into the watched folder.
