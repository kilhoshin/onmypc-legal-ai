/**
 * Search Results Component
 */
import React from 'react';

const SCORE_THRESHOLD = 0.8;

const SearchResults = ({ results, processingTime, onNewSearch }) => {
  if (!results || results.length === 0) {
    return null;
  }

  const filteredResults = results.filter((result) => {
    const rawScore = result?.final_score ?? 0;
    const score = typeof rawScore === 'number' ? rawScore : Number(rawScore);
    return !Number.isNaN(score) && score >= SCORE_THRESHOLD;
  });

  const hasResults = filteredResults.length > 0;

  return (
    <div style={styles.container}>
      {/* Header with back button */}
      <div style={styles.header}>
        <div style={styles.meta}>
          {hasResults
            ? `Showing ${filteredResults.length} results ≥ ${(SCORE_THRESHOLD * 100).toFixed(0)}% • ${processingTime}ms`
            : `No results ≥ ${(SCORE_THRESHOLD * 100).toFixed(0)}% • ${processingTime}ms`}
        </div>
        {onNewSearch && (
          <button onClick={onNewSearch} style={styles.newSearchButton}>
            ← New Search
          </button>
        )}
      </div>

      {/* Results */}
      <div style={styles.results}>
        {hasResults ? (
          filteredResults.map((result, index) => (
            <ResultCard key={index} result={result} index={index} />
          ))
        ) : (
          <div style={styles.noResults}>
            No passages met the 80% relevance threshold. Try refining your query.
          </div>
        )}
      </div>

    </div>
  );
};

const ResultCard = ({ result, index }) => {
  const { chunk, document, bm25_score, vector_score, final_score, match_highlights } = result;

  // Extract filename from path
  const fileName = document?.file_path ? document.file_path.split(/[/\\]/).pop() : 'Unknown';

  // Build location info
  const locationParts = [];
  if (chunk?.page_start) {
    if (chunk.page_start === chunk.page_end) {
      locationParts.push(`Page ${chunk.page_start}`);
    } else {
      locationParts.push(`Pages ${chunk.page_start}-${chunk.page_end}`);
    }
  }
  if (chunk?.section_title) {
    locationParts.push(`§${chunk.section_title}`);
  }
  const locationInfo = locationParts.join(', ');

  // Build section path breadcrumb
  const sectionPath = chunk?.section_path && chunk.section_path.length > 0
    ? chunk.section_path.join(' > ')
    : null;

  return (
    <div style={styles.card}>
      <div style={styles.cardHeader}>
        <div style={styles.cardTitle}>
          <strong style={styles.fileName}>{fileName}</strong>
          {locationInfo && <span style={styles.location}> • {locationInfo}</span>}
        </div>
        <div style={styles.cardMeta}>
          <span style={styles.docType}>{document?.doctype || 'document'}</span>
          {document?.jurisdiction && document.jurisdiction !== 'OTHER' && (
            <span style={styles.jurisdiction}>{document.jurisdiction}</span>
          )}
          <span style={styles.score}>
            Score: {(final_score * 100).toFixed(1)}%
          </span>
        </div>
      </div>

      {sectionPath && (
        <div style={styles.breadcrumb}>{sectionPath}</div>
      )}

      <div style={styles.cardContent}>
        {match_highlights && match_highlights.length > 0
          ? match_highlights.map((highlight, idx) => (
              <div key={idx} style={styles.highlight}>
                {highlight}
              </div>
            ))
          : chunk?.text || 'No content available'
        }
      </div>

      {/* Debug scores - only show in dev */}
      {process.env.NODE_ENV === 'development' && (
        <div style={styles.debugScores}>
          BM25: {bm25_score?.toFixed(3)} | Vector: {vector_score?.toFixed(3)} | Final: {final_score?.toFixed(3)}
        </div>
      )}
    </div>
  );
};

const styles = {
  container: {
    maxWidth: '900px',
    margin: '30px auto',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
  },
  meta: {
    fontSize: '14px',
    color: '#666',
  },
  newSearchButton: {
    padding: '8px 16px',
    fontSize: '14px',
    backgroundColor: '#007bff',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: '500',
  },
  results: {
    display: 'flex',
    flexDirection: 'column',
    gap: '15px',
    marginBottom: '30px',
  },
  noResults: {
    padding: '20px',
    backgroundColor: '#fffde7',
    border: '1px solid #ffe082',
    borderRadius: '8px',
    color: '#8d6e63',
    fontSize: '14px',
  },
  card: {
    backgroundColor: '#fff',
    border: '1px solid #e0e0e0',
    borderRadius: '8px',
    padding: '20px',
    boxShadow: '0 2px 4px rgba(0, 0, 0, 0.05)',
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: '15px',
    flexWrap: 'wrap',
    gap: '10px',
  },
  cardTitle: {
    fontSize: '16px',
    color: '#333',
    lineHeight: '1.5',
  },
  fileName: {
    color: '#007bff',
  },
  location: {
    color: '#666',
    fontSize: '14px',
    fontWeight: 'normal',
  },
  breadcrumb: {
    fontSize: '13px',
    color: '#888',
    marginBottom: '10px',
    fontStyle: 'italic',
  },
  cardMeta: {
    display: 'flex',
    gap: '12px',
    fontSize: '13px',
    color: '#666',
  },
  docType: {
    backgroundColor: '#e3f2fd',
    color: '#1976d2',
    padding: '3px 8px',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: '500',
    textTransform: 'uppercase',
  },
  jurisdiction: {
    backgroundColor: '#f3e5f5',
    color: '#7b1fa2',
    padding: '3px 8px',
    borderRadius: '4px',
    fontSize: '12px',
    fontWeight: '500',
  },
  score: {
    color: '#4caf50',
    fontWeight: 'bold',
    fontSize: '13px',
  },
  highlight: {
    marginBottom: '8px',
    paddingLeft: '10px',
    borderLeft: '3px solid #ffc107',
  },
  debugScores: {
    marginTop: '10px',
    padding: '8px',
    backgroundColor: '#f5f5f5',
    borderRadius: '4px',
    fontSize: '11px',
    color: '#666',
    fontFamily: 'monospace',
  },
  cardContent: {
    fontSize: '14px',
    lineHeight: '1.6',
    color: '#444',
    whiteSpace: 'pre-wrap',
  },
};

export default SearchResults;
