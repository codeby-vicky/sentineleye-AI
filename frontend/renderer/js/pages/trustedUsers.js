const trustedUsersModule = {
    isStreaming: false,
    users: [],

    render() {
        let usersHtml = `
            <div style="text-align: center; color: var(--text-muted); margin-top: 40px;">
                <svg viewBox="0 0 24 24" width="48" height="48" stroke="currentColor" stroke-width="1.5" fill="none" style="margin-bottom: 16px; opacity: 0.5;"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle></svg>
                <h3>No trusted users added yet.</h3>
            </div>
        `;

        if (this.users.length > 0) {
            usersHtml = this.users.map(u => `
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 8px;">
                    <div>
                        <div style="font-weight: 600; font-size: 16px;">${u.name}</div>
                        <div style="font-size: 13px; color: var(--text-muted); text-transform: capitalize;">Role: ${u.relationship}</div>
                    </div>
                    <button class="btn btn-outline btn-remove-user" data-id="${u.id}" style="padding: 6px 12px; border-color: var(--danger-color); color: var(--danger-color);">Remove</button>
                </div>
            `).join('');
        }

        return `
            <div class="page-header" style="margin-bottom: 16px;">
                <button class="btn btn-outline" style="margin-bottom: 8px;" onclick="window.router.navigate('dashboard')">
                    <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" stroke-width="2" fill="none"><line x1="19" y1="12" x2="5" y2="12"></line><polyline points="12 19 5 12 12 5"></polyline></svg>
                    Back to Home
                </button>
                <h1 class="page-title">User Access Control</h1>
                <p class="page-subtitle">Manage people allowed to view your screen securely.</p>
            </div>

            <div class="split-layout">
                <!-- Left: List of Trusted Users -->
                <div class="split-left" style="background: transparent; border: none; flex-direction: column; justify-content: flex-start;">
                    <div class="card" style="width: 100%; height: 100%; display: flex; flex-direction: column;">
                        <h2 style="margin-bottom: 16px;">Authorized Profiles</h2>
                        <div id="users-list" style="flex: 1; overflow-y: auto; background: rgba(0,0,0,0.2); border-radius: 8px; padding: 12px;">
                            ${usersHtml}
                        </div>
                    </div>
                </div>

                <!-- Right: Registration Form & Camera -->
                <div class="split-right">
                    <div class="card" style="flex: 1; display: flex; flex-direction: column;">
                        <h2 style="margin-bottom: 16px;">Add New Profile</h2>
                        
                        <div class="form-group">
                            <label class="form-label">Full Name</label>
                            <input type="text" id="new-user-name" class="form-input" placeholder="e.g. Jane Doe" autocomplete="off">
                        </div>
                        
                        <div class="form-group" style="margin-bottom: 16px;">
                            <label class="form-label">Access Role</label>
                            <select id="new-user-role" class="form-select">
                                <option value="colleague">Colleague (Trusted User)</option>
                                <option value="friend">Friend (Trusted User)</option>
                                <option value="family">Family (Trusted User)</option>
                                <option value="owner">Additional Owner</option>
                            </select>
                        </div>

                        <div style="flex: 1; min-height: 250px; background: #000; border-radius: 8px; margin-bottom: 16px; display: flex; align-items: center; justify-content: center; position: relative; overflow: hidden;">
                            <img id="trusted-video" style="width: 100%; height: 100%; object-fit: cover; display: none;" src="" alt="Camera Feed">
                            <div id="trusted-loading" style="position: absolute; color: white; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                                <div class="spinner"></div>
                                <p>Initializing Camera...</p>
                            </div>
                        </div>
                        
                        <button id="btn-add-user" class="btn btn-primary" style="width: 100%; padding: 16px; font-weight: bold;" disabled>
                            Start Capture
                        </button>
                    </div>
                </div>
            </div>
        `;
    },

    async mount() {
        await this.fetchUsers();
        
        this.onFrameUpdate = this.handleFrameUpdate.bind(this);
        window.socketService.on('setup_frame_update', this.onFrameUpdate);

        document.getElementById('btn-add-user').addEventListener('click', () => this.submitUser());
        
        document.getElementById('new-user-name').addEventListener('input', (e) => {
            document.getElementById('btn-add-user').disabled = e.target.value.trim() === '';
        });

        // Start backend camera
        try {
            await window.apiService.post('/camera/start', { camera_index: 0 });
            this.isStreaming = true;
        } catch (err) {
            console.error(err);
            window.notify.error("Failed to start camera.");
            document.getElementById('trusted-loading').innerHTML = '<p style="color: var(--danger-color);">Camera failed.</p>';
        }
    },

    async fetchUsers() {
        try {
            const data = await window.apiService.get('/users/trusted');
            this.users = data.users || [];
            this.updateUsersList();
        } catch (e) {
            console.error(e);
        }
    },

    updateUsersList() {
        const listContainer = document.getElementById('users-list');
        if (!listContainer) return;
        
        if (this.users.length === 0) {
            listContainer.innerHTML = `
                <div style="text-align: center; color: var(--text-muted); margin-top: 40px;">
                    <svg viewBox="0 0 24 24" width="48" height="48" stroke="currentColor" stroke-width="1.5" fill="none" style="margin-bottom: 16px; opacity: 0.5;"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle></svg>
                    <h3>No trusted users added yet.</h3>
                </div>
            `;
            return;
        }

        listContainer.innerHTML = this.users.map(u => `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 12px; background: rgba(255,255,255,0.05); border-radius: 8px; margin-bottom: 8px;">
                <div>
                    <div style="font-weight: 600; font-size: 16px;">${u.name}</div>
                    <div style="font-size: 13px; color: var(--text-muted); text-transform: capitalize;">Role: ${u.relationship}</div>
                </div>
                <button class="btn btn-outline btn-remove-user" data-id="${u.id}" style="padding: 6px 12px; border-color: var(--danger-color); color: var(--danger-color);">Remove</button>
            </div>
        `).join('');

        document.querySelectorAll('.btn-remove-user').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                const id = e.target.getAttribute('data-id');
                try {
                    await window.apiService.delete('/users/trusted/' + id);
                    window.notify.success("User removed");
                    this.fetchUsers();
                } catch (err) {
                    window.notify.error("Failed to remove user");
                }
            });
        });
    },

    handleFrameUpdate(data) {
        if (!this.isStreaming) return;
        
        const img = document.getElementById('trusted-video');
        const loading = document.getElementById('trusted-loading');
        
        if (data.error) {
            if (loading) loading.innerHTML = `<p style="color: var(--warning-color);">${data.error}</p>`;
            return;
        }
        
        if (img && data.frame) {
            img.style.display = 'block';
            img.src = `data:image/jpeg;base64,${data.frame}`;
            if (loading) loading.style.display = 'none';
        }
    },

    async submitUser() {
        const name = document.getElementById('new-user-name').value.trim();
        const role = document.getElementById('new-user-role').value;
        if (!name) return;

        const btn = document.getElementById('btn-add-user');
        btn.disabled = true;
        btn.innerText = 'Capturing secure frames...';

        try {
            const response = await window.apiService.post('/users/trusted-backend', { name, relationship: role });
            
            if (response.success) {
                window.notify.success('User registered successfully!');
                document.getElementById('new-user-name').value = '';
                btn.innerText = 'Start Capture';
                this.fetchUsers();
            }
        } catch (error) {
            window.notify.error(error.message || 'Registration failed.');
            btn.disabled = false;
            btn.innerText = 'Start Capture';
        }
    },

    async stopCamera() {
        if (this.isStreaming) {
            try {
                await window.apiService.post('/camera/stop', {});
                this.isStreaming = false;
            } catch (e) {}
        }
    },

    async unmount() {
        window.socketService.off('setup_frame_update', this.onFrameUpdate);
        await this.stopCamera();
    }
};

window.router.register('trusted-users', trustedUsersModule);
