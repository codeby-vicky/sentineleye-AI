window.dashboardPage = {
    _statusInterval: null,
    _ownerInterval: null,

    render: function() {
        return `
            <!-- Hero Section -->
            <div class="dashboard-hero">
                <div class="hero-brand">
                    <div class="hero-icon">
                        <svg viewBox="0 0 24 24" width="28" height="28" stroke="var(--accent-primary)" stroke-width="1.5" fill="none">
                            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
                        </svg>
                    </div>
                    <div>
                        <div class="hero-title">SentinelEye AI</div>
                        <div class="hero-subtitle">Intelligent Privacy Protection System</div>
                    </div>
                </div>
                <div class="hero-status connected" id="hero-connection-status">
                    <div class="pulse-dot"></div>
                    <span id="hero-status-text">System Online</span>
                </div>
            </div>

            <!-- Stats Ribbon -->
            <div class="stats-ribbon">
                <div class="stat-kpi">
                    <div class="stat-kpi-icon green">
                        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle></svg>
                    </div>
                    <div class="stat-kpi-info">
                        <div class="stat-kpi-label">Owner</div>
                        <div class="stat-kpi-value" id="kpi-owner">Checking...</div>
                    </div>
                </div>
                <div class="stat-kpi">
                    <div class="stat-kpi-icon blue">
                        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none"><path d="M2 12h4l2-9 5 18 2-9h5"></path></svg>
                    </div>
                    <div class="stat-kpi-info">
                        <div class="stat-kpi-label">Monitoring</div>
                        <div class="stat-kpi-value" id="kpi-monitoring">Idle</div>
                    </div>
                </div>
                <div class="stat-kpi">
                    <div class="stat-kpi-icon amber">
                        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                    </div>
                    <div class="stat-kpi-info">
                        <div class="stat-kpi-label">Threat Level</div>
                        <div class="stat-kpi-value" id="kpi-threat" style="color: var(--success-color);">LOW</div>
                    </div>
                </div>
                <div class="stat-kpi">
                    <div class="stat-kpi-icon purple">
                        <svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>
                    </div>
                    <div class="stat-kpi-info">
                        <div class="stat-kpi-label">System</div>
                        <div class="stat-kpi-value" id="kpi-system" style="color: var(--success-color);">Healthy</div>
                    </div>
                </div>
            </div>

            <!-- Action Cards Grid -->
            <div class="action-grid">
                <!-- Start Monitoring -->
                <div class="action-card card-monitor" id="card-monitoring" onclick="window.router.navigate('monitoring')">
                    <div class="action-card-icon">
                        <svg viewBox="0 0 24 24" width="28" height="28" stroke="var(--accent-primary)" stroke-width="1.5" fill="none"><path d="M2 12h4l2-9 5 18 2-9h5"></path></svg>
                    </div>
                    <h2 id="monitor-card-title">Start Monitoring</h2>
                    <p>Launch real-time privacy shield</p>
                </div>

                <!-- Protection Status -->
                <div class="action-card card-status" id="card-status">
                    <div class="action-card-icon">
                        <svg viewBox="0 0 24 24" width="28" height="28" stroke="var(--success-color)" stroke-width="1.5" fill="none"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                    </div>
                    <h2>Protection Status</h2>
                    <p id="protection-status-text" style="color: var(--text-muted); font-weight: 600;">Idle</p>
                    <div class="card-detail">
                        <span>Threat: <strong id="dash-threat-level" style="color: var(--success-color);">LOW</strong></span>
                        <span>Score: <strong id="dash-threat-score">0</strong></span>
                    </div>
                </div>

                <!-- Setup Owner -->
                <div class="action-card card-setup" onclick="window.router.navigate('setup')">
                    <div class="action-card-icon">
                        <svg viewBox="0 0 24 24" width="28" height="28" stroke="#8b5cf6" stroke-width="1.5" fill="none"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="8.5" cy="7" r="4"></circle><line x1="20" y1="8" x2="20" y2="14"></line><line x1="23" y1="11" x2="17" y2="11"></line></svg>
                    </div>
                    <h2>Setup Owner</h2>
                    <p>Register or update your face profile</p>
                </div>

                <!-- Settings -->
                <div class="action-card card-settings" onclick="window.router.navigate('settings')">
                    <div class="action-card-icon">
                        <svg viewBox="0 0 24 24" width="28" height="28" stroke="#64748b" stroke-width="1.5" fill="none"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                    </div>
                    <h2>Settings</h2>
                    <p>Configure defense rules & preferences</p>
                </div>
            </div>
        `;
    },
    
    mount: function() {
        // Card hover effects
        document.querySelectorAll('.action-card').forEach(card => {
            card.style.transition = 'transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease';
        });
        
        if (window.socketService && window.socketService.connected) {
            window.socketService._updateGlobalStatus(true);
        }

        // Check owner status
        this._checkOwner();
        
        // Poll monitoring status
        this._updateProtectionStatus();
        this._statusInterval = setInterval(() => this._updateProtectionStatus(), 2000);
    },

    async _checkOwner() {
        try {
            const owner = await window.apiService.get('/auth/owner');
            const el = document.getElementById('kpi-owner');
            if (el) {
                el.textContent = owner.name || 'Registered';
                el.style.color = 'var(--success-color)';
            }
        } catch(e) {
            const el = document.getElementById('kpi-owner');
            if (el) {
                el.textContent = 'Not Registered';
                el.style.color = 'var(--warning-color)';
            }
        }
    },

    async _updateProtectionStatus() {
        try {
            const status = await window.apiService.get('/monitoring/status');
            const statusText = document.getElementById('protection-status-text');
            const threatLevel = document.getElementById('dash-threat-level');
            const threatScore = document.getElementById('dash-threat-score');
            const monCard = document.getElementById('card-monitoring');
            const kpiMonitoring = document.getElementById('kpi-monitoring');
            const kpiThreat = document.getElementById('kpi-threat');
            const monTitle = document.getElementById('monitor-card-title');

            if (!statusText) return;

            if (status.active) {
                statusText.textContent = 'Active — Monitoring';
                statusText.style.color = 'var(--success-color)';
                if (kpiMonitoring) { kpiMonitoring.textContent = 'Active'; kpiMonitoring.style.color = 'var(--success-color)'; }
                if (monTitle) monTitle.textContent = 'View Monitor';
            } else {
                statusText.textContent = 'Idle';
                statusText.style.color = 'var(--text-muted)';
                if (kpiMonitoring) { kpiMonitoring.textContent = 'Idle'; kpiMonitoring.style.color = 'var(--text-muted)'; }
                if (monTitle) monTitle.textContent = 'Start Monitoring';
            }

            const level = status.current_threat_level || 'LOW';
            const score = Math.round(status.current_threat_score || 0);
            const colors = { LOW: 'var(--success-color)', MEDIUM: 'var(--warning-color)', HIGH: '#f97316', CRITICAL: 'var(--danger-color)' };
            
            if (threatLevel) {
                threatLevel.textContent = level;
                threatLevel.style.color = colors[level] || 'var(--success-color)';
            }
            if (threatScore) threatScore.textContent = score;
            if (kpiThreat) {
                kpiThreat.textContent = level;
                kpiThreat.style.color = colors[level] || 'var(--success-color)';
            }
        } catch(e) { /* polling errors ignored */ }
    },

    unmount: function() {
        if (this._statusInterval) {
            clearInterval(this._statusInterval);
            this._statusInterval = null;
        }
    }
};

window.router.register('dashboard', window.dashboardPage);
