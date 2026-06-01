const { app, BrowserWindow } = require('electron');

app.whenReady().then(() => {
  const win = new BrowserWindow({
    width: 800,
    height: 600,
    frame: false,
    alwaysOnTop: true
  });
  
  win.setContentProtection(true);
  
  win.loadURL('data:text/html,<html><body style="background: red; color: white;"><h1>Secret Red Window</h1></body></html>');
  
  setTimeout(() => {
    app.quit();
  }, 10000);
});
