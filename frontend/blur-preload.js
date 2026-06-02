const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('blurAPI', {
  onSetIntensity: (callback) => ipcRenderer.on('set-intensity', (event, intensity) => callback(intensity)),
  hideBlur: () => ipcRenderer.invoke('hide-blur-overlay')
});
