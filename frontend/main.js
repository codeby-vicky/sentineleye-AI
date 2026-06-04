const { app, BrowserWindow, ipcMain, shell, Notification } = require('electron');
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
    webPreferences: {
      preload: path.join(__dirname, 'blur-preload.js'),
      nodeIntegration: false,
      contextIsolation: true
    }
  });
  
  blurWindow.setIgnoreMouseEvents(false);
  blurWindow.maximize();
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
  
  ipcMain.handle('lock-workstation', () => {
    // Display sleep instead of workstation lock — preserves owner workflow
    if (process.platform === 'win32') {
      // SC_MONITORPOWER via nircmd (fallback: powershell)
      exec('powershell -Command "(Add-Type -MemberDefinition \\"[DllImport(\\\\\\\"user32.dll\\\\\\\")]public static extern int SendMessage(int hWnd, int hMsg, int wParam, int lParam);\\" -Name a -Namespace b -PassThru)::SendMessage(-1,0x0112,0xF170,2)"');
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
      
      blurWindow.webContents.send('set-intensity', intensity || 'partial');
      blurWindow.show();
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
    // 10 second cooldown per unique title
    if (!notificationCooldowns[title] || (now - notificationCooldowns[title]) > 10000) {
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
