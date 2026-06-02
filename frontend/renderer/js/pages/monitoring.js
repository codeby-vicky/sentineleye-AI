const monitoringModule = {
    isMonitoring: false,

    render() {
        return `
            <div class="page-header" style="margin-bottom: 16px;">
                <button class="btn btn-outline" style="margin-bottom: 8px;" onclick="window.router.navigate('dashboard')">
                    <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
                    Back to Home
                </button>
                <h1 class="page-title">Live Monitoring</h1>
                <p class="page-subtitle">Real-time threat detection and analysis.</p>
            </div>

            <div class="split-layout">
                <!-- Left: Full camera view -->
                <div class="split-left" id="feed-container">
                    <div class="feed-placeholder" id="feed-placeholder" style="color: white; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                        <svg class="radar-icon" viewBox="0 0 24 24" width="64" height="64" stroke="currentColor" stroke-width="1.5" fill="none" style="margin-bottom: 16px;">
                            <circle cx="12" cy="12" r="10"></circle>
                            <circle cx="12" cy="12" r="6"></circle>
                            <circle cx="12" cy="12" r="2"></circle>
                            <line x1="12" y1="12" x2="19.07" y2="4.93"></line>
                        </svg>
                        <p>Monitoring inactive. Start session to begin.</p>
                    </div>
                    <img id="feed-image" class="feed-image" style="width: 100%; height: 100%; object-fit: cover; display: none;" alt="Live Feed">
                </div>

                <!-- Right: Threat Meters and Logs -->
                <div class="split-right">
                    <div class="card threat-meter-container" style="text-align: center; padding: 24px;">
                        <div class="stat-title" style="margin-bottom: 16px; color: var(--text-muted); font-size: 14px; text-transform: uppercase; letter-spacing: 1px;">Threat Level</div>
                        <div class="threat-score-circle" id="threat-score-display" style="font-size: 48px; font-weight: 800; margin-bottom: 8px;">0</div>
                        <h2 id="threat-level-display" style="color: var(--success-color); font-size: 24px; font-weight: 700;">LOW</h2>
                    </div>

                    <div style="display: flex; gap: 16px;">
                        <div class="card" style="flex: 1; text-align: center;">
                            <div class="info-label" style="color: var(--text-muted); font-size: 12px; margin-bottom: 8px; text-transform: uppercase;">Sensitivity</div>
                            <div class="info-value" id="sens-display" style="font-size: 18px; font-weight: 600; color: var(--text-primary);">SAFE</div>
                        </div>
                        <div class="card" style="flex: 1; text-align: center;">
                            <div class="info-label" style="color: var(--text-muted); font-size: 12px; margin-bottom: 8px; text-transform: uppercase;">Active Faces</div>
                            <div class="info-value" id="faces-display" style="font-size: 18px; font-weight: 600; color: var(--text-primary);">0</div>
                        </div>
                    </div>

                    <div class="card" style="flex: 1; display: flex; flex-direction: column; overflow: hidden; padding: 16px;">
                        <h3 style="margin-bottom: 12px; font-size: 16px; color: var(--text-secondary);">Current Observers</h3>
                        <div class="detections-list" id="detections-list" style="flex: 1; overflow-y: auto; background: rgba(0,0,0,0.2); border-radius: 8px; padding: 12px;">
                            <div style="text-align: center; color: var(--text-muted); padding: 20px;">No observers detected</div>
                        </div>
                    </div>

                    <div class="control-panel" style="margin-top: 8px;">
                        <button id="btn-toggle-monitor" class="btn btn-primary" style="width: 100%; padding: 16px; font-size: 18px; font-weight: 600;">START MONITORING</button>
                    </div>
                </div>
            </div>
        `;
    },

    async mount() {
        this.updateHandlers();
        
        // Check current status
        try {
            const status = await window.apiService.get('/monitoring/status');
            this.isMonitoring = status.active;
            this.updateButtonUI();
        } catch (e) {
            console.error(e);
        }

        document.getElementById('btn-toggle-monitor').addEventListener('click', () => this.toggleMonitoring());
    },
    
    updateHandlers() {
        // Bind to socket events
        this.onFrameUpdate = this.handleFrameUpdate.bind(this);
        this.onStatusUpdate = this.handleStatusUpdate.bind(this);
        
        window.socketService.on('frame_update', this.onFrameUpdate);
        window.socketService.on('status_update', this.onStatusUpdate);
    },

    async toggleMonitoring() {
        const btn = document.getElementById('btn-toggle-monitor');
        btn.disabled = true;
        
        try {
            if (this.isMonitoring) {
                await window.apiService.post('/monitoring/stop', {});
                window.notify.info('Monitoring stopped');
            } else {
                await window.apiService.post('/monitoring/start', {});
                window.notify.success('Monitoring started');
                // Auto-minimize after a brief delay
                if (window.system && window.system.minimize) {
                    setTimeout(async () => {
                        try {
                            const settingsResponse = await window.apiService.get('/settings');
                            if (settingsResponse.settings && settingsResponse.settings['auto_minimize'] === 'true') {
                                window.system.minimize();
                            }
                        } catch(e) {}
                    }, 1000);
                }
            }
            this.isMonitoring = !this.isMonitoring;
            this.updateButtonUI();
            
            if (!this.isMonitoring) {
                // Reset UI
                document.getElementById('feed-image').style.display = 'none';
                document.getElementById('feed-placeholder').style.display = 'flex';
                this.updateThreatMeter(0, 'LOW');
                document.getElementById('detections-list').innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 20px;">No observers detected</div>';
            }
        } catch (error) {
            window.notify.error('Failed to toggle monitoring');
        } finally {
            btn.disabled = false;
        }
    },
    
    updateButtonUI() {
        const btn = document.getElementById('btn-toggle-monitor');
        if (this.isMonitoring) {
            btn.className = 'btn btn-danger';
            btn.innerText = 'STOP MONITORING';
        } else {
            btn.className = 'btn btn-primary';
            btn.innerText = 'START MONITORING';
        }
    },

    handleFrameUpdate(data) {
        // Remove strict isMonitoring check here to prevent race conditions
        // where backend emits frames before frontend state syncs
        const img = document.getElementById('feed-image');
        const placeholder = document.getElementById('feed-placeholder');
        
        if (img && data.frame) {
            img.src = `data:image/jpeg;base64,${data.frame}`;
            img.style.display = 'block';
            if (placeholder) placeholder.style.display = 'none';
        }
        
        this.updateThreatMeter(data.threat_score, data.threat_level);
        this.updateDetectionsList(data.detections);
    },
    
    handleStatusUpdate(data) {
        this.isMonitoring = data.active;
        this.updateButtonUI();
        
        const sensEl = document.getElementById('sens-display');
        if (sensEl) {
            sensEl.innerText = data.screen_sensitivity.replace('_', ' ').toUpperCase();
        }
    },
    
    updateThreatMeter(score, level) {
        const scoreEl = document.getElementById('threat-score-display');
        const levelEl = document.getElementById('threat-level-display');
        const containerEl = scoreEl?.parentElement;
        
        if (scoreEl && levelEl && containerEl) {
            scoreEl.innerText = Math.round(score);
            levelEl.innerText = level;
            
            // Reset classes
            containerEl.className = `card threat-meter-container level-${level}`;
            
            // Set text color
            if (level === 'LOW') levelEl.style.color = 'var(--success-color)';
            if (level === 'MEDIUM') levelEl.style.color = 'var(--warning-color)';
            if (level === 'HIGH' || level === 'CRITICAL') levelEl.style.color = 'var(--danger-color)';
        }
    },
    
    updateDetectionsList(detections) {
        const list = document.getElementById('detections-list');
        if (!list) return;
        
        const facesEl = document.getElementById('faces-display');
        if (facesEl) facesEl.innerText = detections.length;
        
        if (!detections || detections.length === 0) {
            list.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 20px;">No observers detected</div>';
            return;
        }
        
        let html = '';
        detections.forEach(det => {
            let badgeClass = 'badge-medium';
            if (det.type === 'owner') badgeClass = 'badge-low';
            if (det.type === 'unknown' || det.type === 'crossing') badgeClass = 'badge-high';
            
            const isLooking = det.gaze_score > 0.6;
            
            html += `
                <div class="detection-item" style="border-left: 3px solid ${isLooking ? 'var(--danger-color)' : 'transparent'}">
                    <div class="det-info">
                        <span class="det-name">${det.identity}</span>
                        <span class="det-type">${Math.round(det.persistence)}s tracking</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span class="det-gaze" style="color: ${isLooking ? 'var(--danger-color)' : 'var(--text-muted)'}">Gaze: ${Math.round(det.gaze_score * 100)}%</span>
                        <span class="badge ${badgeClass}">${det.type.toUpperCase()}</span>
                    </div>
                </div>
            `;
        });
        
        list.innerHTML = html;
    },

    unmount() {
        window.socketService.off('frame_update', this.onFrameUpdate);
        window.socketService.off('status_update', this.onStatusUpdate);
    }
};

window.router.register('monitoring', monitoringModule);
