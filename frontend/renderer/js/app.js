// Core App Initialization

document.addEventListener('DOMContentLoaded', async () => {
    // Setup window controls
    document.getElementById('btn-minimize').addEventListener('click', () => {
        window.system.minimize();
    });
    
    document.getElementById('btn-maximize').addEventListener('click', () => {
        window.system.maximize();
    });
    
    document.getElementById('btn-close').addEventListener('click', () => {
        window.system.close();
    });

    // Initialize WebSockets
    window.socketService.connect();

    // Register sound player
    window.system.onPlaySound((type) => {
        const audio = document.getElementById(`audio-${type}`);
        if (audio) {
            audio.currentTime = 0;
            audio.play().catch(e => console.warn('Audio play failed:', e));
        }
    });
    
    // Register socket global defense listener
    window.socketService.on('threat_detected', (data) => {
        if (data.play_sound) {
            let soundType = 'alert';
            if (data.level === 'HIGH') soundType = 'warning';
            if (data.level === 'CRITICAL') soundType = 'critical';
            window.system.playSound(soundType);
        }
        
        // Use native Windows notification instead of in-app toast
        if (window.system.showNotification) {
            window.system.showNotification(`${data.level} Threat`, data.reason);
        } else {
            window.notify.warning(`${data.level} Threat: ${data.reason}`, 'Security Alert');
        }
    });

    window.socketService.on('defense_activated', (data) => {
        if (data.action === 'blur_show') {
            window.system.showBlurOverlay(data.intensity, data.bounds);
            // Don't spam notifications for blur unless it's new
            if (window.system.showNotification) {
                // We'll let the threat alert handle the notification to avoid spam, but we can log it internally
                window.notify.info(`Privacy screen activated`, 'Defense Protocol');
            }
        } else if (data.action === 'blur_hide') {
            window.system.hideBlurOverlay();
        }
    });

    // App Initialization Flow
    const loadingScreen = document.getElementById('loading-screen');
    const loadingStatus = document.getElementById('loading-status');
    
    async function checkBackendHealth() {
        try {
            const health = await window.apiService.get('/health');
            if (health.backend && health.camera && health.database) {
                loadingScreen.classList.add('hidden');
                
                // Check owner status after health is good
                try {
                    await window.apiService.get('/auth/owner');
                    window.router.navigate('dashboard');
                } catch (error) {
                    window.router.navigate('setup');
                }
                return true;
            } else {
                loadingStatus.textContent = 'Waiting for modules...';
                return false;
            }
        } catch (error) {
            loadingStatus.textContent = 'Backend starting...';
            return false;
        }
    }

    // Start polling health every 1 second
    const pollInterval = setInterval(async () => {
        const isHealthy = await checkBackendHealth();
        if (isHealthy) {
            clearInterval(pollInterval);
        }
    }, 1000);
    
    // Initial check
    checkBackendHealth();
});
