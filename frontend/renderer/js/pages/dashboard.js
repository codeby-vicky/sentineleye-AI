window.dashboardPage = {
    render: function() {
        return `
            <div class="page-header" style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <h1 class="page-title">SentinelEye AI</h1>
                    <p class="page-subtitle">Intelligent Privacy Protection & Shoulder Surfing Detection</p>
                </div>
                <div class="status-indicator" style="display: flex; align-items: center; gap: 8px; background: rgba(16, 185, 129, 0.1); padding: 8px 16px; border-radius: 20px; color: #10b981; font-weight: 500;">
                    <div style="width: 8px; height: 8px; border-radius: 50%; background: #10b981; box-shadow: 0 0 8px #10b981;"></div>
                    <span id="global-status-text">Backend Connected</span>
                </div>
            </div>

            <div class="dashboard-grid">
                <!-- Monitor Card -->
                <div class="card dashboard-card" onclick="window.router.navigate('monitoring')" style="cursor: pointer; position: relative; overflow: hidden; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 40px 20px;">
                    <div style="position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: var(--primary-color);"></div>
                    <svg viewBox="0 0 24 24" width="48" height="48" stroke="var(--primary-color)" stroke-width="1.5" fill="none" style="margin-bottom: 16px;"><path d="M2 12h4l2-9 5 18 2-9h5"></path></svg>
                    <h2 style="font-size: 24px; margin-bottom: 8px;">Start Monitoring</h2>
                    <p style="color: var(--text-muted);">Launch real-time privacy shield</p>
                </div>

                <!-- Trusted Users Card -->
                <div class="card dashboard-card" onclick="window.router.navigate('trusted-users')" style="cursor: pointer; position: relative; overflow: hidden; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 40px 20px;">
                    <div style="position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: var(--warning-color);"></div>
                    <svg viewBox="0 0 24 24" width="48" height="48" stroke="var(--warning-color)" stroke-width="1.5" fill="none" style="margin-bottom: 16px;"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
                    <h2 style="font-size: 24px; margin-bottom: 8px;">Trusted Users</h2>
                    <p style="color: var(--text-muted);">Manage authorized profiles</p>
                </div>

                <!-- Registration Card -->
                <div class="card dashboard-card" onclick="window.router.navigate('setup')" style="cursor: pointer; position: relative; overflow: hidden; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 40px 20px;">
                    <div style="position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: #8b5cf6;"></div>
                    <svg viewBox="0 0 24 24" width="48" height="48" stroke="#8b5cf6" stroke-width="1.5" fill="none" style="margin-bottom: 16px;"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>
                    <h2 style="font-size: 24px; margin-bottom: 8px;">Setup Owner</h2>
                    <p style="color: var(--text-muted);">Register or update your face</p>
                </div>

                <!-- Settings Card -->
                <div class="card dashboard-card" onclick="window.router.navigate('settings')" style="cursor: pointer; position: relative; overflow: hidden; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 40px 20px;">
                    <div style="position: absolute; top: 0; left: 0; width: 100%; height: 4px; background: #64748b;"></div>
                    <svg viewBox="0 0 24 24" width="48" height="48" stroke="#64748b" stroke-width="1.5" fill="none" style="margin-bottom: 16px;"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                    <h2 style="font-size: 24px; margin-bottom: 8px;">Settings</h2>
                    <p style="color: var(--text-muted);">Configure defense rules</p>
                </div>
            </div>
        `;
    },
    
    mount: function() {
        const cards = document.querySelectorAll('.dashboard-card');
        cards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-5px)';
            });
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0)';
            });
        });
        
        // Initial status update if socket exists
        if (window.socketService && window.socketService.connected) {
            window.socketService._updateGlobalStatus(true);
        }
    },

    unmount: function() {
        // Nothing to clean up
    }
};

window.router.register('dashboard', window.dashboardPage);
