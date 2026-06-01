window.dashboardPage = {
    render: async function() {
        const container = document.getElementById('main-content');
        container.innerHTML = `
            <div class="page-header">
                <h1 class="page-title">SentinelEye AI</h1>
                <p class="page-subtitle">Intelligent Privacy Protection</p>
                <div style="margin-top: 16px; display: inline-flex; align-items: center; gap: 8px; background: rgba(16, 185, 129, 0.1); padding: 8px 16px; border-radius: 20px; border: 1px solid rgba(16, 185, 129, 0.2);">
                    <div class="status-indicator" style="width: 8px; height: 8px; border-radius: 50%; background-color: var(--success-color); box-shadow: 0 0 8px var(--success-color);"></div>
                    <span id="global-status-text" style="color: var(--success-color); font-weight: 500; font-size: 14px;">Backend Connected</span>
                </div>
            </div>
            
            <div class="dashboard-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 24px; max-width: 1200px; margin: 0 auto;">
                
                <div class="card dashboard-card" style="cursor: pointer; transition: transform 0.2s;" onclick="window.router.navigate('monitoring')">
                    <div style="font-size: 32px; color: var(--accent-primary); margin-bottom: 16px;">
                        <svg viewBox="0 0 24 24" width="48" height="48" stroke="currentColor" stroke-width="1.5" fill="none"><path d="M23 7l-7 5 7 5V7z"></path><rect x="1" y="5" width="15" height="14" rx="2" ry="2"></rect></svg>
                    </div>
                    <h3 style="font-size: 20px; font-weight: 600; margin-bottom: 8px;">Start Monitoring</h3>
                    <p style="color: var(--text-muted); font-size: 14px;">Launch real-time privacy defense against shoulder surfing.</p>
                </div>

                <div class="card dashboard-card" style="cursor: pointer; transition: transform 0.2s;" onclick="window.router.navigate('settings')">
                    <div style="font-size: 32px; color: var(--success-color); margin-bottom: 16px;">
                        <svg viewBox="0 0 24 24" width="48" height="48" stroke="currentColor" stroke-width="1.5" fill="none"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
                    </div>
                    <h3 style="font-size: 20px; font-weight: 600; margin-bottom: 8px;">Privacy Priority</h3>
                    <p style="color: var(--text-muted); font-size: 14px;">Teach SentinelEye what content is privacy-sensitive using NLP.</p>
                </div>

                <div class="card dashboard-card" style="cursor: pointer; transition: transform 0.2s;" onclick="window.router.navigate('setup')">
                    <div style="font-size: 32px; color: var(--warning-color); margin-bottom: 16px;">
                        <svg viewBox="0 0 24 24" width="48" height="48" stroke="currentColor" stroke-width="1.5" fill="none"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
                    </div>
                    <h3 style="font-size: 20px; font-weight: 600; margin-bottom: 8px;">Setup Owner</h3>
                    <p style="color: var(--text-muted); font-size: 14px;">Recalibrate your owner face embeddings.</p>
                </div>

                <div class="card dashboard-card" style="cursor: pointer; transition: transform 0.2s;" onclick="window.router.navigate('settings')">
                    <div style="font-size: 32px; color: var(--text-secondary); margin-bottom: 16px;">
                        <svg viewBox="0 0 24 24" width="48" height="48" stroke="currentColor" stroke-width="1.5" fill="none"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>
                    </div>
                    <h3 style="font-size: 20px; font-weight: 600; margin-bottom: 8px;">Settings</h3>
                    <p style="color: var(--text-muted); font-size: 14px;">Configure privacy levels, OCR, and alarms.</p>
                </div>
            </div>
        `;
        
        // Add hover effects via JS since it's inline styled
        const cards = document.querySelectorAll('.dashboard-card');
        cards.forEach(c => {
            c.addEventListener('mouseenter', () => { c.style.transform = 'translateY(-4px)'; c.style.borderColor = 'var(--accent-primary)'; });
            c.addEventListener('mouseleave', () => { c.style.transform = 'translateY(0)'; c.style.borderColor = 'var(--border-color)'; });
        });
    },

    destroy: function() {
        // Cleanup if needed
    }
};

window.router.register('dashboard', window.dashboardPage);
