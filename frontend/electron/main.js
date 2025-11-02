/**
 * OnMyPC Legal AI - Electron Main Process
 */
const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn } = require('child_process');
const fs = require('fs');

const APP_DISPLAY_NAME = 'OnMyPC Legal AI';

// Backend server process
let pythonProcess = null;
let mainWindow = null;

// Determine if running in development or production
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

// Backend configuration
const BACKEND_PORT = 8000;
const BACKEND_URL = `http://localhost:${BACKEND_PORT}`;

/**
 * Start Python backend server
 */
function startBackendServer() {
  return new Promise((resolve, reject) => {
    console.log('[Backend] Starting Python server...');

    let pythonPath;
    let backendPath;

    let workingDir;
    let runtimeEnv = {};

    if (isDev) {
      // Development: use conda environment Python
      const os = require('os');
      const condaEnvPath = path.join(os.homedir(), 'miniconda3', 'envs', 'legalai', 'python.exe');
      const condaEnvPath2 = path.join(os.homedir(), 'anaconda3', 'envs', 'legalai', 'python.exe');

      // Try conda environment first, fallback to system python
      if (fs.existsSync(condaEnvPath)) {
        pythonPath = condaEnvPath;
        console.log('[Backend] Using miniconda environment');
      } else if (fs.existsSync(condaEnvPath2)) {
        pythonPath = condaEnvPath2;
        console.log('[Backend] Using anaconda environment');
      } else {
        pythonPath = 'python';
        console.log('[Backend] Using system Python (conda env not found)');
      }

      backendPath = path.join(__dirname, '..', '..', 'backend', 'main.py');
      workingDir = path.join(__dirname, '..', '..');
    } else {
      // Production: use bundled Python runtime
      const resourcesPath = process.resourcesPath;
      const pythonDir = path.join(resourcesPath, 'python');
      pythonPath = path.join(pythonDir, 'python.exe');
      backendPath = path.join(resourcesPath, 'backend', 'main.py');

      if (!fs.existsSync(pythonPath)) {
        const error = `Bundled Python runtime not found: ${pythonPath}`;
        console.error('[Backend]', error);
        dialog.showErrorBox(
          'Backend Error',
          `${error}\n\nRun scripts/prepare_portable_env.py to create the runtime.`
        );
        reject(new Error(error));
        return;
      }

      runtimeEnv = {
        PYTHONHOME: pythonDir,
        PYTHONPATH: path.join(resourcesPath, 'backend'),
        WEB_STATIC_DIR: path.join(resourcesPath, 'web'),
      };
      workingDir = resourcesPath;
    }

    console.log('[Backend] Python path:', pythonPath);
    console.log('[Backend] Backend path:', backendPath);

    // Check if backend file exists
    if (!fs.existsSync(backendPath)) {
      const error = `Backend file not found: ${backendPath}`;
      console.error('[Backend]', error);
      dialog.showErrorBox('Backend Error', error);
      reject(new Error(error));
      return;
    }

    // Start Python process
    const spawnEnv = {
      ...process.env,
      PYTHONUNBUFFERED: '1',
      ...runtimeEnv,
    };

    pythonProcess = spawn(pythonPath, [backendPath], {
      cwd: workingDir,
      env: spawnEnv,
    });

    // Handle stdout
    pythonProcess.stdout.on('data', (data) => {
      const message = data.toString().trim();
      console.log('[Backend]', message);

      // Check if server is ready
      if (message.includes('Uvicorn running on') || message.includes('Application startup complete')) {
        console.log('[Backend] Server is ready!');
        resolve();
      }
    });

    // Handle stderr
    pythonProcess.stderr.on('data', (data) => {
      console.error('[Backend Error]', data.toString().trim());
    });

    // Handle process exit
    pythonProcess.on('exit', (code, signal) => {
      console.log(`[Backend] Process exited with code ${code}, signal ${signal}`);
      pythonProcess = null;

      if (code !== 0 && mainWindow) {
        dialog.showErrorBox(
          'Backend Error',
          `Python backend crashed with code ${code}. Please check the logs.`
        );
      }
    });

    // Handle process error
    pythonProcess.on('error', (err) => {
      console.error('[Backend] Failed to start:', err);
      dialog.showErrorBox(
        'Backend Error',
        `Failed to start Python backend:\n${err.message}\n\nMake sure Python is installed.`
      );
      reject(err);
    });

    // Timeout after 30 seconds
    setTimeout(() => {
      if (pythonProcess) {
        console.log('[Backend] Assuming server is ready (timeout)');
        resolve();
      }
    }, 30000);
  });
}

/**
 * Stop Python backend server
 */
function stopBackendServer() {
  if (pythonProcess) {
    console.log('[Backend] Stopping server...');
    pythonProcess.kill();
    pythonProcess = null;
  }
}

/**
 * Create main window
 */
function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    minWidth: 800,
    minHeight: 600,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js'),
    },
    icon: path.join(__dirname, 'resources', 'icon.png'),
    title: APP_DISPLAY_NAME,
    backgroundColor: '#ffffff',
  });

  // Load the app from backend server
  console.log('[App] Loading from backend:', BACKEND_URL);
  mainWindow.loadURL(BACKEND_URL);

  // Open DevTools in development
  if (isDev) {
    mainWindow.webContents.openDevTools();
  }

  // Handle window close
  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

/**
 * App ready
 */
app.whenReady().then(async () => {
  console.log('[App] Starting OnMyPC Legal AI...');
  console.log('[App] Version:', app.getVersion());
  console.log('[App] Is Dev:', isDev);

  try {
    // Start backend server
    await startBackendServer();

    // Create window
    createWindow();

    console.log('[App] Application ready!');
  } catch (error) {
    console.error('[App] Startup error:', error);
    dialog.showErrorBox(
      'Startup Error',
      `Failed to start application:\n${error.message}`
    );
    app.quit();
  }
});

/**
 * All windows closed
 */
app.on('window-all-closed', () => {
  stopBackendServer();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

/**
 * App will quit
 */
app.on('will-quit', () => {
  stopBackendServer();
});

/**
 * Activate (macOS)
 */
app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

/**
 * IPC Handlers
 */

// Get backend URL
ipcMain.handle('get-backend-url', () => {
  return BACKEND_URL;
});

// Select directory
ipcMain.handle('select-directory', async () => {
  const result = await dialog.showOpenDialog(mainWindow, {
    properties: ['openDirectory'],
  });

  if (result.canceled) {
    return null;
  }

  return result.filePaths[0];
});

// Show message box
ipcMain.handle('show-message', async (event, options) => {
  const result = await dialog.showMessageBox(mainWindow, options);
  return result;
});

// Get app info
ipcMain.handle('get-app-info', () => {
  return {
    name: APP_DISPLAY_NAME,
    version: app.getVersion(),
    isDev: isDev,
  };
});
