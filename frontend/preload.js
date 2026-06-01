const { contextBridge, ipcRenderer } = require('electron');

// Expose safe APIs to the renderer process
contextBridge.exposeInMainWorld('system', {
  // Window controls
  minimize: () => ipcRenderer.invoke('window-minimize'),
  maximize: () => ipcRenderer.invoke('window-maximize'),
  close: () => ipcRenderer.invoke('window-close'),
  
  // Defense actions
  lockWorkstation: () => ipcRenderer.invoke('lock-workstation'),
  showBlurOverlay: (intensity, bounds) => ipcRenderer.invoke('show-blur-overlay', {intensity, bounds}),
  hideBlurOverlay: () => ipcRenderer.invoke('hide-blur-overlay'),
  showNotification: (title, body) => ipcRenderer.invoke('show-notification', {title, body}),
  
  // Sounds
  playSound: (type) => ipcRenderer.invoke('play-sound', type),
  onPlaySound: (callback) => ipcRenderer.on('trigger-sound', (_event, type) => callback(type))
});

contextBridge.exposeInMainWorld('api', {
  getBackendUrl: () => 'http://127.0.0.1:5000'
});
