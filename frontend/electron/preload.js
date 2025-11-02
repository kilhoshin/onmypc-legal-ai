/**
 * OnMyPC Legal AI - Electron Preload Script
 */
const { contextBridge, ipcRenderer } = require('electron');

// Expose protected methods to renderer process
contextBridge.exposeInMainWorld('electronAPI', {
  // Get backend URL
  getBackendUrl: () => ipcRenderer.invoke('get-backend-url'),

  // Select directory
  selectDirectory: () => ipcRenderer.invoke('select-directory'),

  // Show message box
  showMessage: (options) => ipcRenderer.invoke('show-message', options),

  // Get app info
  getAppInfo: () => ipcRenderer.invoke('get-app-info'),
});

console.log('[Preload] Electron API exposed to renderer');
