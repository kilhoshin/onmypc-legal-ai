/**
 * OnMyPC Legal AI - Main App
 */
import React, { useState, useEffect } from 'react';
import apiService from './services/api';
import EULADialog from './components/EULADialog';
import FolderSelector from './components/FolderSelector';
import IndexingProgress from './components/IndexingProgress';
import SearchBar from './components/SearchBar';
import SearchResults from './components/SearchResults';

function App() {
  // State
  const [status, setStatus] = useState('loading');
  const [eulaAccepted, setEulaAccepted] = useState(false);
  const [eulaText, setEulaText] = useState('');
  const [folderSelected, setFolderSelected] = useState(false);
  const [selectedFolder, setSelectedFolder] = useState('');
  const [indexStats, setIndexStats] = useState({ total_documents: 0, total_chunks: 0 });
  const [isIndexing, setIsIndexing] = useState(false);
  const [isSearching, setIsSearching] = useState(false);
  const [searchResults, setSearchResults] = useState(null);
  const [appInfo, setAppInfo] = useState({ name: 'OnMyPC Legal AI', version: '1.0.0' });
  const [showSettings, setShowSettings] = useState(false);
  const [indexedFolders, setIndexedFolders] = useState([]);

  const totalTrackedDocuments = indexedFolders.reduce(
    (sum, folder) => sum + (folder.document_count || 0),
    0
  );
  const displayDocumentTotal = Math.max(indexStats.total_documents || 0, totalTrackedDocuments);
  // Load initial status
  useEffect(() => {
    loadStatus();
    loadAppInfo();
  }, []);

  const loadAppInfo = async () => {
    if (window.electronAPI) {
      const info = await window.electronAPI.getAppInfo();
      setAppInfo({
        ...info,
        name: 'OnMyPC Legal AI',
      });
    }
  };

  const loadStatus = async () => {
    try {
      const statusData = await apiService.getStatus();
      setStatus(statusData.status);
      setEulaAccepted(statusData.eula_accepted);
      setIndexStats({
        total_documents: statusData.total_documents,
        total_chunks: statusData.total_chunks,
      });

      // If knowledge base is already loaded, skip folder selection
      if (statusData.knowledge_base_loaded) {
        setFolderSelected(true);
        await loadFolders(true);
      } else {
        setFolderSelected(false);
        setSelectedFolder('');
      }

      // Load EULA if not accepted
      if (!statusData.eula_accepted) {
        const eulaData = await apiService.getEULA();
        setEulaText(eulaData.text);
      }

      return statusData;
    } catch (error) {
      console.error('Failed to load status:', error);
      setStatus('error');
      return null;
    }
  };

  const loadFolders = async (setDefaultSelection = false) => {
    try {
      const foldersData = await apiService.getFolders();
      const folders = foldersData.folders || [];
      setIndexedFolders(folders);

      if (setDefaultSelection && folders.length > 0) {
        setSelectedFolder(folders[0].path);
      }
    } catch (error) {
      console.error('Failed to load folders:', error);
    }
  };

  const handleAcceptEULA = async () => {
    try {
      await apiService.acceptEULA();
      setEulaAccepted(true);
      setStatus('ready');
      // Don't auto-start indexing - wait for folder selection
    } catch (error) {
      console.error('Failed to accept EULA:', error);
      alert('Failed to accept EULA. Please try again.');
    }
  };

  const handleDeclineEULA = () => {
    if (window.electronAPI) {
      window.electronAPI.showMessage({
        type: 'info',
        title: 'EULA Required',
        message: 'You must accept the EULA to use this application.',
        buttons: ['OK'],
      });
    } else {
      alert('You must accept the EULA to use this application.');
    }
  };

  const handleFolderSelected = async (folder) => {
    setSelectedFolder(folder);
    setFolderSelected(true);
    startIndexing(folder);
  };

  const handleChangeFolder = () => {
    setShowSettings(false);
    setFolderSelected(false);
    setIsIndexing(false);
  };

  const handleRemoveFolder = async (folderPath) => {
    const confirmRemoval = window.confirm(
      `Remove the folder:\n${folderPath}\n\nAll documents from this folder will be deleted from the knowledge base and the indexes will be rebuilt. Continue?`
    );
    if (!confirmRemoval) {
      return;
    }

    try {
      setIsIndexing(true);
      await apiService.removeFolder(folderPath);
      await loadFolders();
      const statusData = await loadStatus();
      const refreshedStats = await apiService.getIndexStats();
      setIndexStats(refreshedStats);
      if (!statusData || !statusData.knowledge_base_loaded) {
        setFolderSelected(false);
        setSelectedFolder('');
        setSearchResults(null);
      }
    } catch (error) {
      console.error('Failed to remove folder:', error);
      alert('Failed to remove folder. Please try again.');
    } finally {
      setIsIndexing(false);
    }
  };

  const startIndexing = async (folder) => {
    setIsIndexing(true);
    try {
      await apiService.startIndexing(folder);

      // Poll for indexing completion
      const pollInterval = setInterval(async () => {
        const stats = await apiService.getIndexStats();
        setIndexStats(stats);

        // Check if indexing is complete (simple heuristic)
        if (stats.total_documents > 0) {
          clearInterval(pollInterval);
          setIsIndexing(false);
          // Reload folder list after indexing
          loadFolders();
        }
      }, 2000);

      // Stop polling after 5 minutes
      setTimeout(() => {
        clearInterval(pollInterval);
        setIsIndexing(false);
      }, 300000);
    } catch (error) {
      console.error('Failed to start indexing:', error);
      setIsIndexing(false);
    }
  };

  const handleSearch = async (query) => {
    setIsSearching(true);
    setSearchResults(null);

    try {
      const response = await apiService.query(query);
      setSearchResults(response);
    } catch (error) {
      console.error('Search failed:', error);
      alert('Search failed. Please try again.');
    } finally {
      setIsSearching(false);
    }
  };

  const handleNewSearch = () => {
    setSearchResults(null);
  };

  // Render loading state
  if (status === 'loading') {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading...</div>
      </div>
    );
  }

  // Render error state
  if (status === 'error') {
    return (
      <div style={styles.container}>
        <div style={styles.error}>
          <h2>Connection Error</h2>
          <p>Failed to connect to backend server. Please restart the application.</p>
        </div>
      </div>
    );
  }

  return (
    <div style={styles.container}>
      {/* EULA Dialog */}
      {!eulaAccepted && (
        <EULADialog
          eulaText={eulaText}
          onAccept={handleAcceptEULA}
          onDecline={handleDeclineEULA}
        />
      )}

      {/* Header */}
      <header style={styles.header}>
        <div style={styles.headerTop}>
          <h1 style={styles.title}>{appInfo.name}</h1>
          {eulaAccepted && folderSelected && (
            <button onClick={() => setShowSettings(!showSettings)} style={styles.settingsButton}>
              ⚙️ Settings
            </button>
          )}
        </div>
        <p style={styles.subtitle}>Your Personal Legal AI Assistant - 100% Local & Private</p>
        {folderSelected && (
          <div style={styles.stats}>
            <span>{displayDocumentTotal} documents indexed</span>
            <span>•</span>
            <span>{indexStats.total_chunks} searchable chunks</span>
            {indexedFolders.length > 0 && (
              <>
                <span>•</span>
                <span>
                  📁
                  {indexedFolders.length === 1
                    ? ` ${indexedFolders[0].path}`
                    : ` ${indexedFolders.length} folders indexed`}
                </span>
              </>
            )}
          </div>
        )}
      </header>

      {/* Settings Dropdown */}
      {showSettings && (
        <div style={styles.settingsPanel}>
          <div style={styles.settingsHeader}>
            <h3 style={styles.settingsTitle}>Settings</h3>
            <button onClick={() => setShowSettings(false)} style={styles.closeButton}>
              ✕
            </button>
          </div>

          {/* Folder List */}
          {indexedFolders.length > 0 && (
            <div style={styles.folderSection}>
              <h4 style={styles.sectionTitle}>Indexed Folders</h4>
              <div style={styles.folderList}>
                {indexedFolders.map((folder, index) => (
                  <div key={index} style={styles.folderItem}>
                    <div style={styles.folderInfo}>
                      <div style={styles.folderPath}>📁 {folder.path}</div>
                      <div style={styles.folderMeta}>
                        {folder.document_count} documents • Last indexed: {new Date(folder.last_indexed).toLocaleString()}
                      </div>
                    </div>
                    <button
                      style={styles.removeFolderButton}
                      onClick={() => handleRemoveFolder(folder.path)}
                      title="Remove folder"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Actions */}
          <div style={styles.settingsActions}>
            <button onClick={handleChangeFolder} style={styles.addFolderButton}>
              ➕ Add Document Folder
            </button>
            <button onClick={() => startIndexing(selectedFolder)} style={styles.reindexButton}>
              🔄 Re-index All Documents
            </button>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main style={styles.main}>
        {!folderSelected ? (
          <FolderSelector
            onFolderSelected={handleFolderSelected}
            currentFolder={selectedFolder}
            isIndexing={isIndexing}
          />
        ) : isIndexing ? (
          <IndexingProgress stats={indexStats} />
        ) : (
          <>
            <SearchBar onSearch={handleSearch} isSearching={isSearching} />
            {searchResults && (
              <SearchResults
                results={searchResults.results}
                processingTime={searchResults.total_time_ms}
                onNewSearch={handleNewSearch}
              />
            )}
          </>
        )}
      </main>

      {/* Footer */}
      <footer style={styles.footer}>
        <a
          href="https://buymeacoffee.com/giroshin"
          target="_blank"
          rel="noopener noreferrer"
          style={styles.coffeeButton}
        >
          ☕ Buy Kilho Shin a Coffee
        </a>
        <p style={styles.footerText}>
          v{appInfo.version} • All processing happens locally on your computer • Contact: kilhoshin1978@gmail.com
        </p>
      </footer>
    </div>
  );
}

const styles = {
  container: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#f5f5f5',
  },
  loading: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100vh',
    fontSize: '20px',
    color: '#666',
  },
  error: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    height: '100vh',
    textAlign: 'center',
    color: '#dc3545',
  },
  header: {
    backgroundColor: '#fff',
    padding: '30px 20px',
    borderBottom: '2px solid #e0e0e0',
    textAlign: 'center',
  },
  headerTop: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    gap: '20px',
    position: 'relative',
  },
  title: {
    margin: '0 0 10px 0',
    fontSize: '36px',
    color: '#007bff',
    fontWeight: 'bold',
  },
  settingsButton: {
    position: 'absolute',
    right: '20px',
    padding: '8px 16px',
    fontSize: '14px',
    backgroundColor: '#6c757d',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  settingsPanel: {
    backgroundColor: '#fff',
    padding: '20px',
    borderBottom: '1px solid #e0e0e0',
  },
  settingsHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: '20px',
  },
  settingsTitle: {
    margin: 0,
    fontSize: '18px',
    color: '#333',
  },
  closeButton: {
    padding: '5px 10px',
    fontSize: '16px',
    backgroundColor: 'transparent',
    color: '#666',
    border: 'none',
    cursor: 'pointer',
  },
  folderSection: {
    marginBottom: '20px',
  },
  sectionTitle: {
    margin: '0 0 10px 0',
    fontSize: '14px',
    color: '#666',
    fontWeight: '600',
  },
  folderList: {
    display: 'flex',
    flexDirection: 'column',
    gap: '10px',
  },
  folderItem: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    gap: '12px',
    padding: '12px 16px',
    backgroundColor: '#f8f9fa',
    borderRadius: '6px',
    border: '1px solid #e0e0e0',
    position: 'relative',
  },
  folderInfo: {
    display: 'flex',
    flexDirection: 'column',
    gap: '5px',
  },
  folderPath: {
    fontSize: '14px',
    color: '#333',
    fontWeight: '500',
    wordBreak: 'break-all',
  },
  folderMeta: {
    fontSize: '12px',
    color: '#666',
  },
  removeFolderButton: {
    backgroundColor: '#fff',
    border: '1px solid #dc3545',
    color: '#dc3545',
    cursor: 'pointer',
    fontSize: '14px',
    fontWeight: '700',
    lineHeight: '1',
    padding: '4px 8px',
    borderRadius: '12px',
    height: '26px',
    minWidth: '26px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  settingsActions: {
    display: 'flex',
    justifyContent: 'center',
    gap: '10px',
  },
  addFolderButton: {
    padding: '10px 20px',
    fontSize: '14px',
    backgroundColor: '#007bff',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  reindexButton: {
    padding: '10px 20px',
    fontSize: '14px',
    backgroundColor: '#28a745',
    color: '#fff',
    border: 'none',
    borderRadius: '4px',
    cursor: 'pointer',
  },
  subtitle: {
    margin: '0 0 15px 0',
    fontSize: '16px',
    color: '#666',
  },
  stats: {
    display: 'flex',
    gap: '10px',
    justifyContent: 'center',
    fontSize: '14px',
    color: '#999',
  },
  main: {
    flex: 1,
    padding: '40px 20px',
    overflow: 'auto',
  },
  footer: {
    backgroundColor: '#fff',
    padding: '20px',
    borderTop: '2px solid #e0e0e0',
    textAlign: 'center',
  },
  coffeeButton: {
    display: 'inline-block',
    padding: '10px 20px',
    backgroundColor: '#FFDD00',
    color: '#000',
    textDecoration: 'none',
    borderRadius: '5px',
    fontWeight: 'bold',
    marginBottom: '10px',
    transition: 'background-color 0.2s',
  },
  footerText: {
    margin: 0,
    fontSize: '12px',
    color: '#999',
  },
};

export default App;
