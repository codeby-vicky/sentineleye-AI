const settingsModule = {
    render() {
        return `
            <style>
                .settings-grid {
                    display: grid;
                    grid-template-columns: 1fr;
                    max-width: 800px;
                    margin: 24px auto;
                    gap: 24px;
                }
                .settings-card {
                    background: var(--surface-light);
                    border: 1px solid var(--border-color);
                    border-radius: 12px;
                    padding: 24px;
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                }
                .settings-card-header {
                    font-size: 16px;
                    font-weight: 700;
                    color: var(--text-primary);
                    margin-bottom: 8px;
                    border-bottom: 1px solid rgba(255,255,255,0.05);
                    padding-bottom: 12px;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }
                .settings-row-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    gap: 16px;
                    padding: 8px 0;
                }
                .settings-row-info {
                    flex: 1;
                }
                .settings-row-title {
                    font-size: 14px;
                    font-weight: 600;
                    color: var(--text-primary);
                }
                .settings-row-desc {
                    font-size: 12px;
                    color: var(--text-muted);
                    margin-top: 4px;
                }
                .settings-control-box {
                    min-width: 150px;
                    display: flex;
                    justify-content: flex-end;
                }
            </style>
            <div class="page-header animate-slide-up stagger-1">
                <button class="btn btn-outline" style="margin-bottom: 16px;" onclick="window.router.navigate('dashboard')">
                    <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
                    Back to Home
                </button>
                <h1 class="page-title">Settings</h1>
                <p class="page-subtitle">Configure system behavior and privacy protocols.</p>
            </div>

            <div class="settings-scroll-container" style="overflow-y: auto; height: calc(100vh - 180px); padding-right: 12px;">
                <div class="settings-grid animate-fade-in stagger-2">
                    
                    <!-- 1. Monitoring Settings -->
                    <div class="settings-card">
                        <div class="settings-card-header">1. Threat Monitoring</div>
                        
                        <div class="settings-row-item">
                            <div class="settings-row-info">
                                <div class="settings-row-title">Monitoring Sensitivity</div>
                                <div class="settings-row-desc">Adjust how quickly the system reacts to shoulder surfing.</div>
                            </div>
                            <div class="settings-control-box">
                                <select id="monitoring_sensitivity" class="form-select setting-input">
                                    <option value="low">Low (Forgiving)</option>
                                    <option value="medium">Medium (Balanced)</option>
                                    <option value="high">High (Strict)</option>
                                </select>
                            </div>
                        </div>

                        <div class="settings-row-item">
                            <div class="settings-row-info">
                                <div class="settings-row-title">Auto Minimize SentinelEye</div>
                                <div class="settings-row-desc">Automatically hide the app when monitoring begins.</div>
                            </div>
                            <div class="settings-control-box"><label class="toggle-switch"><input type="checkbox" id="auto_minimize" class="setting-toggle"><span class="toggle-slider"></span></label></div>
                        </div>
                    </div>

                    <!-- 2. Privacy Priority -->
                    <div class="settings-card">
                        <div class="settings-card-header">2. Smart Privacy Engine</div>
                        
                        <div class="settings-row-item">
                            <div class="settings-row-info">
                                <div class="settings-row-title">Privacy Sensitivity</div>
                                <div class="settings-row-desc">Instruct the NLP engine on how aggressively to protect on-screen content.</div>
                            </div>
                            <div class="settings-control-box">
                                <select id="privacy_sensitivity" class="form-select setting-input">
                                    <option value="low">Low</option>
                                    <option value="medium">Medium</option>
                                    <option value="high">High</option>
                                    <option value="aggressive">Aggressive (Protect Everything)</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <!-- 3. Alert Settings -->
                    <div class="settings-card">
                        <div class="settings-card-header">3. Alert Preferences</div>

                        <div class="settings-row-item">
                            <div class="settings-row-info"><div class="settings-row-title">Desktop Notifications</div></div>
                            <div class="settings-control-box"><label class="toggle-switch"><input type="checkbox" id="toast_notifications" class="setting-toggle"><span class="toggle-slider"></span></label></div>
                        </div>
                        
                        <div class="settings-row-item">
                            <div class="settings-row-info"><div class="settings-row-title">Sound Alerts</div></div>
                            <div class="settings-control-box"><label class="toggle-switch"><input type="checkbox" id="sound_enabled" class="setting-toggle"><span class="toggle-slider"></span></label></div>
                        </div>
                    </div>

                    <!-- 4. Performance Settings -->
                    <div class="settings-card">
                        <div class="settings-card-header">4. Performance Mode</div>

                        <div class="settings-row-item">
                            <div class="settings-row-info">
                                <div class="settings-row-title">System Load Management</div>
                                <div class="settings-row-desc">Optimize CPU and GPU usage based on your hardware capabilities.</div>
                            </div>
                            <div class="settings-control-box">
                                <select id="perf_mode" class="form-select setting-input">
                                    <option value="battery">Battery Saver</option>
                                    <option value="balanced">Balanced</option>
                                    <option value="high">High Performance</option>
                                </select>
                            </div>
                        </div>
                    </div>

                    <div style="display: flex; justify-content: flex-end; margin-top: 16px; margin-bottom: 32px; width: 100%;">
                        <button id="btn-save-settings" class="btn btn-primary">Save Settings</button>
                    </div>
                </div>
            </div>
        `;
    },

    async mount() {
        await this.loadSettings();
        document.getElementById('btn-save-settings').addEventListener('click', () => this.saveSettings());
    },
    
    async loadSettings() {
        try {
            const data = await window.apiService.get('/settings');
            const settings = data.settings;
            
            // Set input values
            document.querySelectorAll('.setting-input').forEach(input => {
                if (settings[input.id] !== undefined) {
                    input.value = settings[input.id];
                }
            });
            
            // Set toggle values
            document.querySelectorAll('.setting-toggle').forEach(toggle => {
                if (settings[toggle.id] !== undefined) {
                    toggle.checked = settings[toggle.id] === 'true';
                }
            });
            
        } catch (error) {
            window.notify.error('Failed to load settings');
        }
    },
    
    async saveSettings() {
        const btn = document.getElementById('btn-save-settings');
        btn.disabled = true;
        btn.innerText = 'Saving...';
        
        try {
            const newSettings = {};
            
            document.querySelectorAll('.setting-input').forEach(input => {
                newSettings[input.id] = input.value;
            });
            
            document.querySelectorAll('.setting-toggle').forEach(toggle => {
                newSettings[toggle.id] = toggle.checked ? 'true' : 'false';
            });
            
            await window.apiService.put('/settings', newSettings);
            window.notify.success('Settings saved successfully');
        } catch (error) {
            window.notify.error('Failed to save settings');
        } finally {
            btn.disabled = false;
            btn.innerText = 'Save Settings';
        }
    },

    unmount() {}
};

window.router.register('settings', settingsModule);
