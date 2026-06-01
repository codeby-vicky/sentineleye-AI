const { app, BrowserWindow, ipcMain, shell, Notification, desktopCapturer } = require('electron');
const path = require('path');
const { spawn, exec } = require('child_process');
const http = require('http');

let mainWindow;
let blurWindow;
let pythonProcess;

// Ensure single instance
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
}

// Required for Native Windows Toast Notifications
app.setAppUserModelId('SentinelEye.Privacy.AI');

// RTX 2050 4GB VRAM constraint optimizations
app.commandLine.appendSwitch('enable-low-end-device-mode'); // Optimizes tile memory and rasterization
app.commandLine.appendSwitch('limit-fps', '30'); // Prevents unnecessary 60+ FPS rendering
app.commandLine.appendSwitch('js-flags', '--max-old-space-size=512'); // Limits JS heap
app.commandLine.appendSwitch('disable-gpu-memory-buffer-video-frames'); // Saves GPU memory

function startPythonBackend() {
  console.log('Starting Python backend...');
  let pythonExecutable = process.platform === 'win32' ? 'python' : 'python3';
  const specificPath = 'C:\\Users\\ASUS\\AppData\\Local\\Programs\\Python\\Python310\\python.exe';
  const fs = require('fs');
  if (fs.existsSync(specificPath)) {
      pythonExecutable = specificPath;
  }
  
  const backendPath = path.join(__dirname, '..', 'backend', 'run.py');
  
  pythonProcess = spawn(pythonExecutable, [backendPath], {
    cwd: path.join(__dirname, '..', 'backend'),
    env: { ...process.env, PYTHONUNBUFFERED: '1' }
  });

  pythonProcess.stdout.on('data', (data) => {
    console.log(`Backend stdout: ${data}`);
  });

  pythonProcess.stderr.on('data', (data) => {
    console.error(`Backend stderr: ${data}`);
  });

  pythonProcess.on('close', (code) => {
    console.log(`Backend process exited with code ${code}`);
  });
}

function waitForBackend(callback) {
  const maxRetries = 120;
  let retries = 0;

  const interval = setInterval(() => {
    http.get('http://127.0.0.1:5000/api/health', (res) => {
      if (res.statusCode === 200) {
        clearInterval(interval);
        console.log('Backend is ready!');
        callback(true);
      }
    }).on('error', (err) => {
      retries++;
      if (retries >= maxRetries) {
        clearInterval(interval);
        console.error('Failed to connect to backend after 120 attempts');
        // Do not load UI if backend fails to connect
        callback(false);
      }
    });
  }, 1000);
}

function createWindows() {
  // Main Window
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 768,
    frame: false, // Custom titlebar
    backgroundColor: '#0f172a',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false
    }
  });

    // Blur Overlay Window (initially hidden, transparent)
    blurWindow = new BrowserWindow({
      width: 800,
      height: 600,
      frame: false,
      transparent: true,
      alwaysOnTop: true,
      show: false,
      skipTaskbar: true,
      focusable: false, // CRITICAL: Prevent OS from stealing focus
      webPreferences: {
        nodeIntegration: true, // Required for WebRTC desktop capture
        contextIsolation: false // Required for direct require('electron') in HTML
      }
    });
    
    // CRITICAL: Hide blur window from screen capture so it can capture the desktop behind it
    blurWindow.setContentProtection(true);
  
  // CRITICAL: Let clicks pass through to the protected app beneath
  blurWindow.setIgnoreMouseEvents(true, { forward: true });
  blurWindow.maximize();
  blurWindow.setAlwaysOnTop(true, "screen-saver"); // Forces overlay above even full-screen apps
  blurWindow.loadFile('blur-overlay.html');

  // Load main UI
  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

  // Open external links in default browser
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  // Setup IPC Handlers
  ipcMain.handle('window-minimize', () => mainWindow.minimize());
  ipcMain.handle('window-maximize', () => {
    if (mainWindow.isMaximized()) {
      mainWindow.unmaximize();
    } else {
      mainWindow.maximize();
    }
  });
  ipcMain.handle('window-close', () => mainWindow.close());
  
  // Provide desktop source ID to renderer for WebRTC stream
  ipcMain.handle('get-desktop-source-id', async () => {
    try {
      const sources = await desktopCapturer.getSources({ types: ['screen'] });
      // Usually screen 1 is sources[0], but we can return the first screen found
      return sources[0].id;
    } catch (e) {
      console.error('Failed to get desktop sources:', e);
      return null;
    }
  });
  
  ipcMain.handle('lock-workstation', () => {
    if (process.platform === 'win32') {
      exec('rundll32.exe user32.dll,LockWorkStation');
    }
  });

  ipcMain.handle('show-blur-overlay', (event, data) => {
    if (blurWindow) {
      const { intensity, bounds } = data;
      
      if (bounds) {
        // Blur specific bounds (targeted app)
        blurWindow.unmaximize();
        // Allow tiny offset in Windows so it doesn't get obscured
        blurWindow.setBounds({
          x: bounds.x,
          y: bounds.y,
          width: bounds.w,
          height: bounds.h
        });
      } else {
        // Full screen blur
        blurWindow.maximize();
      }
      
      // Pass the bounds to renderer so it can perfectly align the WebRTC video margin
      blurWindow.webContents.send('set-intensity', { intensity: intensity || 'partial', bounds: bounds });
      
      if (!blurWindow.isVisible()) {
        blurWindow.showInactive(); // Use showInactive to prevent stealing foreground focus
      }
    }
  });

  ipcMain.handle('hide-blur-overlay', () => {
    if (blurWindow) {
      blurWindow.hide();
    }
  });

  ipcMain.handle('play-sound', (event, type) => {
    // In a real app, we'd play native sounds here, or tell the renderer to play HTML5 audio
    mainWindow.webContents.send('trigger-sound', type);
  });
  
  // Notification cooldown tracker
  const notificationCooldowns = {};
  
  ipcMain.handle('show-notification', (event, data) => {
    const { title, body } = data;
    const now = Date.now();
    // 5 second cooldown per unique title
    if (!notificationCooldowns[title] || (now - notificationCooldowns[title]) > 5000) {
        new Notification({ title, body, silent: true }).show();
        notificationCooldowns[title] = now;
    }
  });
}

app.whenReady().then(() => {
  startPythonBackend();
  
  // Wait for Flask to boot before showing UI
  waitForBackend((success) => {
    if (success) {
      createWindows();
    } else {
      const { dialog } = require('electron');
      dialog.showErrorBox('Initialization Failed', 'The SentinelEye AI backend failed to start within 120 seconds. Please check logs and try again.');
      app.quit();
    }
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindows();
  });
});

// Cleanup on exit
app.on('will-quit', () => {
  if (pythonProcess) {
    if (process.platform === 'win32') {
      exec(`taskkill /pid ${pythonProcess.pid} /T /F`);
    } else {
      pythonProcess.kill('SIGTERM');
    }
  }
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
