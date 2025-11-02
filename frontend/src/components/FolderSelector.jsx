/**
 * Folder Selector Component
 */
import React, { useState } from 'react';

const FolderSelector = ({ onFolderSelected, currentFolder, isIndexing }) => {
  const [selectedFolder, setSelectedFolder] = useState(currentFolder || '');

  const handleSelectFolder = async () => {
    if (window.electronAPI && window.electronAPI.selectDirectory) {
      const folder = await window.electronAPI.selectDirectory();
      if (folder) {
        setSelectedFolder(folder);
      }
    } else {
      alert('Folder selection is only available in desktop app');
    }
  };

  const handleStartIndexing = () => {
    if (selectedFolder) {
      onFolderSelected(selectedFolder);
    } else {
      alert('Please select a folder first');
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.content}>
        <h2 style={styles.title}>Select Document Folder</h2>
        <p style={styles.description}>
          Choose a folder containing your legal documents (PDF, DOCX, TXT)
        </p>

        <div style={styles.folderSelector}>
          <input
            type="text"
            value={selectedFolder}
            placeholder="No folder selected"
            readOnly
            style={styles.input}
          />
          <button onClick={handleSelectFolder} style={styles.browseButton}>
            Browse...
          </button>
        </div>

        <div style={styles.actions}>
          <button
            onClick={handleStartIndexing}
            disabled={!selectedFolder || isIndexing}
            style={{
              ...styles.startButton,
              ...((!selectedFolder || isIndexing) ? styles.buttonDisabled : {}),
            }}
          >
            {isIndexing ? 'Indexing...' : 'Start Indexing'}
          </button>
        </div>

        <div style={styles.note}>
          <strong>Note:</strong> Indexing may take 3-5 minutes depending on the number of documents.
          You can change this folder later in settings.
        </div>
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
    maxWidth: '600px',
    width: '100%',
  },
  title: {
    fontSize: '28px',
    color: '#333',
    marginBottom: '10px',
    textAlign: 'center',
  },
  description: {
    fontSize: '16px',
    color: '#666',
    marginBottom: '30px',
    textAlign: 'center',
  },
  folderSelector: {
    display: 'flex',
    gap: '10px',
    marginBottom: '20px',
  },
  input: {
    flex: 1,
    padding: '12px',
    fontSize: '14px',
    border: '2px solid #e0e0e0',
    borderRadius: '4px',
    backgroundColor: '#f5f5f5',
  },
  browseButton: {
    padding: '12px 30px',
    fontSize: '14px',
    backgroundColor: '#007bff',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
    fontWeight: 'bold',
  },
  actions: {
    textAlign: 'center',
    marginBottom: '20px',
  },
  startButton: {
    padding: '15px 50px',
    fontSize: '18px',
    backgroundColor: '#28a745',
    color: '#fff',
    border: 'none',
    borderRadius: '8px',
    cursor: 'pointer',
    fontWeight: 'bold',
  },
  buttonDisabled: {
    backgroundColor: '#ccc',
    cursor: 'not-allowed',
  },
  note: {
    fontSize: '14px',
    color: '#666',
    padding: '15px',
    backgroundColor: '#f8f9fa',
    borderRadius: '4px',
    borderLeft: '4px solid #007bff',
  },
};

export default FolderSelector;
