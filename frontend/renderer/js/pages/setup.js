const setupModule = {
    isStreaming: false,

    render() {
        return `
            <div class="page-header" style="margin-bottom: 16px;">
                <button class="btn btn-outline" style="margin-bottom: 8px;" onclick="window.router.navigate('dashboard')">
                    <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
                    Back to Home
                </button>
                <h1 class="page-title">Owner Registration</h1>
                <p class="page-subtitle">Multi-angle facial registration for high-accuracy tracking.</p>
            </div>

            <div class="split-layout">
                <!-- Left: Full camera view -->
                <div class="split-left">
                    <img id="setup-video" style="width: 100%; height: 100%; object-fit: cover;" src="" alt="Camera Feed">
                    <div id="camera-loading" style="position: absolute; color: white; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                        <div class="spinner"></div>
                        <p>Initializing Secure Camera Stream...</p>
                    </div>
                </div>

                <!-- Right: Controls -->
                <div class="split-right">
                    <div class="card" style="flex: 1; display: flex; flex-direction: column; justify-content: center;">
                        <h2 style="margin-bottom: 24px; font-size: 24px;">Registration Details</h2>
                        
                        <div class="form-group" style="margin-bottom: 32px;">
                            <label class="form-label">Full Name</label>
                            <input type="text" id="owner-name" class="form-input" style="font-size: 18px; padding: 12px;" placeholder="e.g. John Doe" autocomplete="off">
                        </div>

                        <div style="background: rgba(255,255,255,0.05); padding: 16px; border-radius: 8px; margin-bottom: 32px;">
                            <h3 style="margin-bottom: 12px; font-size: 14px; color: var(--text-muted);">Instructions</h3>
                            <ul style="color: var(--text-secondary); font-size: 14px; padding-left: 20px; line-height: 1.6;">
                                <li>Ensure adequate lighting.</li>
                                <li>Follow the on-screen prompts to turn your head.</li>
                                <li>We will capture your face from 5 distinct angles.</li>
                            </ul>
                        </div>
                        
                        <div id="capture-status" style="margin-bottom: 24px; font-size: 18px; font-weight: 600; color: var(--warning-color); text-align: center; min-height: 24px;"></div>

                        <button id="btn-capture" class="btn btn-primary" style="padding: 16px; font-size: 18px; font-weight: 600;" disabled>
                            Start Multi-Angle Capture
                        </button>
                    </div>
                </div>
            </div>
        `;
    },

    async mount() {
        this.onFrameUpdate = this.handleFrameUpdate.bind(this);
        window.socketService.on('setup_frame_update', this.onFrameUpdate);

        document.getElementById('btn-capture').addEventListener('click', () => this.submitRegistration());
        
        document.getElementById('owner-name').addEventListener('input', (e) => {
            const btn = document.getElementById('btn-capture');
            if (e.target.value.trim() !== '') {
                btn.disabled = false;
            } else {
                btn.disabled = true;
            }
        });

        // Start backend camera
        try {
            await window.apiService.post('/camera/start', { camera_index: 0 });
            this.isStreaming = true;
        } catch (err) {
            console.error(err);
            window.notify.error("Failed to start backend camera stream.");
            document.getElementById('camera-loading').innerHTML = '<p style="color: var(--danger-color);">Camera failed to initialize.</p>';
        }
    },

    handleFrameUpdate(data) {
        if (!this.isStreaming) return;
        
        const img = document.getElementById('setup-video');
        const loading = document.getElementById('camera-loading');
        
        if (data.error) {
            if (loading) {
                loading.innerHTML = `<p style="color: var(--warning-color); text-align: center;">${data.error}</p>`;
            }
            return;
        }
        
        if (img && data.frame) {
            img.src = `data:image/jpeg;base64,${data.frame}`;
            if (loading) loading.style.display = 'none';
        }
    },
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    },

    async submitRegistration() {
        const name = document.getElementById('owner-name').value.trim();
        if (!name) return;

        const btn = document.getElementById('btn-capture');
        const statusEl = document.getElementById('capture-status');
        
        btn.disabled = true;
        document.getElementById('owner-name').disabled = true;
        
        const angles = ["Front", "Left Tilt", "Right Tilt", "Slightly Up", "Slightly Down"];
        
        try {
            for (let i = 0; i < angles.length; i++) {
                const angle = angles[i];
                btn.innerText = `Capturing Angle ${i+1}/${angles.length}`;
                statusEl.innerText = `Please look: ${angle}`;
                
                // Give user a moment to adjust
                await this.sleep(2000);
                
                statusEl.innerText = `Capturing ${angle}...`;
                const response = await window.apiService.post('/auth/capture-angle', { name, angle });
                if (!response.success) {
                    throw new Error(response.message);
                }
            }
            
            statusEl.innerText = "Finalizing Registration...";
            btn.innerText = 'Processing embeddings...';
            
            const finalRes = await window.apiService.post('/auth/finalize-registration', { name });
            if (finalRes.success) {
                statusEl.innerText = "Success!";
                statusEl.style.color = "var(--success-color)";
                window.notify.success('Owner registered successfully!');
                await this.stopCamera();
                
                setTimeout(async () => {
                    try {
                        const settingsResponse = await window.apiService.get('/settings');
                        const settings = settingsResponse.settings || {};
                        
                        await window.apiService.post('/monitoring/start', {});
                        window.notify.info('Background monitoring activated natively', 'SentinelEye Guard');
                        
                        if (settings['auto_minimize'] === 'true' && window.system && window.system.minimize) {
                            await window.system.minimize();
                        }
                    } catch (e) {
                        console.error('Failed to auto-start monitoring', e);
                    }
                    window.router.navigate('dashboard');
                }, 1000);
            }
        } catch (error) {
            window.notify.error(error.message || 'Failed to capture. Please try again.');
            statusEl.innerText = "Capture failed.";
            btn.disabled = false;
            document.getElementById('owner-name').disabled = false;
            btn.innerText = 'Start Multi-Angle Capture';
        }
    },

    async stopCamera() {
        if (this.isStreaming) {
            try {
                await window.apiService.post('/camera/stop', {});
                this.isStreaming = false;
            } catch (e) {
                console.error("Failed to stop camera", e);
            }
        }
    },

    async unmount() {
        window.socketService.off('setup_frame_update', this.onFrameUpdate);
        await this.stopCamera();
    }
};

window.router.register('setup', setupModule);
