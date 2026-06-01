class SocketService {
    constructor() {
        this.socket = null;
        this.handlers = new Map();
        this.connected = false;
    }

    connect() {
        const url = window.api.getBackendUrl();
        console.log(`Connecting to WebSocket at ${url}...`);
        
        this.socket = io(url);

        this.socket.on('connect', () => {
            console.log('WebSocket connected');
            this.connected = true;
            this._updateGlobalStatus(true);
            this._trigger('connect');
        });

        this.socket.on('disconnect', () => {
            console.log('WebSocket disconnected');
            this.connected = false;
            this._updateGlobalStatus(false);
            this._trigger('disconnect');
        });

        // Register core event handlers
        this.socket.on('status_update', (data) => this._trigger('status_update', data));
        this.socket.on('frame_update', (data) => this._trigger('frame_update', data));
        this.socket.on('setup_frame_update', (data) => this._trigger('setup_frame_update', data));
        this.socket.on('threat_detected', (data) => this._trigger('threat_detected', data));
        this.socket.on('defense_activated', (data) => this._trigger('defense_activated', data));
    }

    on(event, callback) {
        if (!this.handlers.has(event)) {
            this.handlers.set(event, []);
        }
        this.handlers.get(event).push(callback);
    }

    off(event, callback) {
        if (this.handlers.has(event)) {
            const cbs = this.handlers.get(event);
            const idx = cbs.indexOf(callback);
            if (idx > -1) {
                cbs.splice(idx, 1);
            }
        }
    }

    _trigger(event, data) {
        if (this.handlers.has(event)) {
            this.handlers.get(event).forEach(cb => cb(data));
        }
    }

    _updateGlobalStatus(isConnected) {
        const indicator = document.querySelector('.status-indicator');
        const text = document.getElementById('global-status-text');
        
        if (indicator && text) {
            if (isConnected) {
                indicator.style.backgroundColor = 'var(--success-color)';
                text.textContent = 'Backend Connected';
            } else {
                indicator.style.backgroundColor = 'var(--danger-color)';
                indicator.style.boxShadow = '0 0 8px var(--danger-color)';
                text.textContent = 'Backend Disconnected';
            }
        }
    }
}

window.socketService = new SocketService();
