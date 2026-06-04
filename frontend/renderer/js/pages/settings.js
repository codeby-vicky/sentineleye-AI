const settingsModule = {
    render() {
        return `
            <style>
                .settings-container {
                    max-width: 800px;
                    margin: 24px auto;
                    display: flex;
                    flex-direction: column;
                    gap: 24px;
                }
                .profile-section {
                    display: flex;
                    flex-direction: column;
                    gap: 16px;
                }
                .profile-cards {
                    display: grid;
                    grid-template-columns: repeat(3, 1fr);
                    gap: 16px;
                }
                .profile-card {
                    background: var(--surface-light);
                    border: 2px solid var(--border-color);
                    border-radius: 16px;
                    padding: 24px 20px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    text-align: center;
                    position: relative;
                    overflow: hidden;
                }
                .profile-card:hover {
                    border-color: var(--accent-color);
                    transform: translateY(-2px);
                    box-shadow: 0 8px 24px rgba(99, 102, 241, 0.15);
                }
                .profile-card.active {
                    border-color: var(--accent-color);
                    background: linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(139, 92, 246, 0.04));
                }
                .profile-card.active::after {
                    content: '✓ Active';
                    position: absolute;
                    top: 12px;
                    right: 12px;
                    font-size: 11px;
                    font-weight: 700;
                    color: var(--success-color);
                    background: rgba(16, 185, 129, 0.1);
                    padding: 2px 8px;
                    border-radius: 6px;
                }
                .profile-icon {
                    font-size: 36px;
                    margin-bottom: 12px;
                }
                .profile-name {
                    font-size: 16px;
                    font-weight: 700;
                    color: var(--text-primary);
                    margin-bottom: 6px;
                }
                .profile-desc {
                    font-size: 12px;
                    color: var(--text-muted);
                    line-height: 1.5;
                }
                .profile-badge {
                    display: inline-block;
                    margin-top: 12px;
                    font-size: 11px;
                    font-weight: 600;
                    padding: 4px 10px;
                    border-radius: 8px;
                    letter-spacing: 0.3px;
                }
                .badge-low { background: rgba(34, 197, 94, 0.1); color: #22c55e; }
                .badge-balanced { background: rgba(99, 102, 241, 0.1); color: #6366f1; }
                .badge-high { background: rgba(239, 68, 68, 0.1); color: #ef4444; }

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
                .settings-row-info { flex: 1; }
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
                .advanced-toggle {
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    cursor: pointer;
                    font-size: 13px;
                    color: var(--text-muted);
                    padding: 8px 0;
                    user-select: none;
                }
                .advanced-toggle:hover { color: var(--text-primary); }
                .advanced-toggle svg {
                    transition: transform 0.3s ease;
                }
                .advanced-toggle.open svg {
                    transform: rotate(90deg);
                }
                .advanced-body {
                    display: none;
                    flex-direction: column;
                    gap: 16px;
                    animation: fadeIn 0.3s ease;
                }
                .advanced-body.visible {
                    display: flex;
                }
                @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
            </style>

            <div class="page-header animate-slide-up stagger-1">
                <button class="btn btn-outline" style="margin-bottom: 16px;" onclick="window.router.navigate('dashboard')">
                    <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
                    Back to Home
                </button>
                <h1 class="page-title">Settings</h1>
                <p class="page-subtitle">Choose a protection profile that fits your needs.</p>
            </div>

            <div class="settings-container" style="overflow-y: auto; height: calc(100vh - 180px); padding-right: 12px;">
                <!-- Performance Profile Selection -->
                <div class="profile-section animate-fade-in stagger-2">
                    <div class="profile-cards">
                        <div class="profile-card" id="profile-low" onclick="settingsModule.selectProfile('low')">
                            <div class="profile-icon">⚡</div>
                            <div class="profile-name">Low Performance</div>
                            <div class="profile-desc">Minimal resource usage. Best for older systems or battery saving.</div>
                            <span class="profile-badge badge-low">Lightweight</span>
                        </div>
                        <div class="profile-card" id="profile-balanced" onclick="settingsModule.selectProfile('balanced')">
                            <div class="profile-icon">⚖️</div>
                            <div class="profile-name">Balanced</div>
                            <div class="profile-desc">Recommended for most users. Good accuracy with moderate resource usage.</div>
                            <span class="profile-badge badge-balanced">Recommended</span>
                        </div>
                        <div class="profile-card" id="profile-high" onclick="settingsModule.selectProfile('high')">
                            <div class="profile-icon">🛡️</div>
                            <div class="profile-name">High Security</div>
                            <div class="profile-desc">Maximum protection. Frequent analysis and strongest blur. Higher resource usage.</div>
                            <span class="profile-badge badge-high">Maximum</span>
                        </div>
                    </div>
                </div>

                <!-- Quick Toggles -->
                <div class="settings-card animate-fade-in stagger-3">
                    <div class="settings-card-header">Quick Settings</div>
                    <div class="settings-row-item">
                        <div class="settings-row-info"><div class="settings-row-title">Desktop Notifications</div><div class="settings-row-desc">Show alerts when threats are detected.</div></div>
                        <div class="settings-control-box"><label class="toggle-switch"><input type="checkbox" id="toast_notifications" class="setting-toggle"><span class="toggle-slider"></span></label></div>
                    </div>
                    <div class="settings-row-item">
                        <div class="settings-row-info"><div class="settings-row-title">Sound Alerts</div><div class="settings-row-desc">Play audio cues on detection events.</div></div>
                        <div class="settings-control-box"><label class="toggle-switch"><input type="checkbox" id="sound_enabled" class="setting-toggle"><span class="toggle-slider"></span></label></div>
                    </div>
                </div>

                <!-- Advanced Settings (collapsed) -->
                <div class="settings-card animate-fade-in stagger-4">
                    <div class="advanced-toggle" id="advanced-toggle" onclick="settingsModule.toggleAdvanced()">
                        <svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none"><polyline points="9 18 15 12 9 6"></polyline></svg>
                        Advanced Settings
                    </div>
                    <div class="advanced-body" id="advanced-body">
                        <div class="settings-row-item">
                            <div class="settings-row-info"><div class="settings-row-title">Camera Index</div><div class="settings-row-desc">Select which camera to use (0 = default).</div></div>
                            <div class="settings-control-box"><select id="camera_index" class="form-select setting-input"><option value="0">0 (Default)</option><option value="1">1</option><option value="2">2</option></select></div>
                        </div>
                        <div class="settings-row-item">
                            <div class="settings-row-info"><div class="settings-row-title">Monitoring Sensitivity</div><div class="settings-row-desc">How quickly the system reacts to shoulder surfing.</div></div>
                            <div class="settings-control-box"><select id="monitoring_sensitivity" class="form-select setting-input"><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option></select></div>
                        </div>
                        <div class="settings-row-item">
                            <div class="settings-row-info"><div class="settings-row-title">Privacy Sensitivity</div><div class="settings-row-desc">NLP engine aggressiveness for content protection.</div></div>
                            <div class="settings-control-box"><select id="privacy_sensitivity" class="form-select setting-input"><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="aggressive">Aggressive</option></select></div>
                        </div>
                    </div>
                </div>

                <div style="display: flex; justify-content: flex-end; margin-bottom: 32px;">
                    <button id="btn-save-settings" class="btn btn-primary">Save Settings</button>
                </div>
            </div>
        `;
    },

    async mount() {
        await this.loadSettings();
        document.getElementById('btn-save-settings').addEventListener('click', () => this.saveSettings());
    },

    toggleAdvanced() {
        const toggle = document.getElementById('advanced-toggle');
        const body = document.getElementById('advanced-body');
        toggle.classList.toggle('open');
        body.classList.toggle('visible');
    },

    async selectProfile(name) {
        // Visual update
        document.querySelectorAll('.profile-card').forEach(c => c.classList.remove('active'));
        const card = document.getElementById(`profile-${name}`);
        if (card) card.classList.add('active');

        try {
            await window.apiService.post(`/settings/profile/${name}`);
            window.notify.success(`${name.charAt(0).toUpperCase() + name.slice(1)} profile applied`);
        } catch (e) {
            window.notify.error('Failed to apply profile');
        }
    },

    async loadSettings() {
        try {
            const data = await window.apiService.get('/settings');
            const settings = data.settings;

            // Highlight active profile
            const activeProfile = settings.performance_profile || 'balanced';
            document.querySelectorAll('.profile-card').forEach(c => c.classList.remove('active'));
            const activeCard = document.getElementById(`profile-${activeProfile}`);
            if (activeCard) activeCard.classList.add('active');

            // Set input values
            document.querySelectorAll('.setting-input').forEach(input => {
                if (settings[input.id] !== undefined) input.value = settings[input.id];
            });

            // Set toggle values
            document.querySelectorAll('.setting-toggle').forEach(toggle => {
                if (settings[toggle.id] !== undefined) toggle.checked = settings[toggle.id] === 'true';
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
