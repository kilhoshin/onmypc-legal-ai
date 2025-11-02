/**
 * Indexing Progress Component
 */
import React from 'react';

const IndexingProgress = ({ stats }) => {
  return (
    <div style={styles.container}>
      <div style={styles.content}>
        <div style={styles.spinner}></div>
        <h3 style={styles.title}>Building Knowledge Base...</h3>
        <p style={styles.description}>
          Analyzing your legal documents and creating searchable index
        </p>
        <div style={styles.stats}>
          <div style={styles.stat}>
            <strong>{stats.total_documents}</strong> documents
          </div>
          <div style={styles.stat}>
            <strong>{stats.total_chunks}</strong> chunks
          </div>
        </div>
        <p style={styles.note}>This process runs once. Please wait...</p>
      </div>
    </div>
  );
};

const styles = {
  container: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '400px',
    padding: '40px',
  },
  content: {
    textAlign: 'center',
    maxWidth: '500px',
  },
  spinner: {
    width: '60px',
    height: '60px',
    border: '5px solid #f3f3f3',
    borderTop: '5px solid #007bff',
    borderRadius: '50%',
    margin: '0 auto 20px',
    animation: 'spin 1s linear infinite',
  },
  title: {
    fontSize: '24px',
    color: '#333',
    marginBottom: '10px',
  },
  description: {
    fontSize: '16px',
    color: '#666',
    marginBottom: '20px',
  },
  stats: {
    display: 'flex',
    gap: '30px',
    justifyContent: 'center',
    marginBottom: '20px',
  },
  stat: {
    fontSize: '14px',
    color: '#666',
  },
  note: {
    fontSize: '14px',
    color: '#999',
    fontStyle: 'italic',
  },
};

// Add keyframe animation
const styleSheet = document.styleSheets[0];
styleSheet.insertRule(`
  @keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
  }
`, styleSheet.cssRules.length);

export default IndexingProgress;
