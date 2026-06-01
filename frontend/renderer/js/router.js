class Router {
    constructor() {
        this.routes = new Map();
        this.currentRoute = null;
        this.mainContent = document.getElementById('main-content');
        
        // Setup sidebar click listeners
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const route = e.currentTarget.dataset.route;
                this.navigate(route);
            });
        });
    }

    register(path, module) {
        this.routes.set(path, module);
    }

    async navigate(path) {
        if (!this.routes.has(path)) {
            console.error(`Route not found: ${path}`);
            return;
        }

        // Update sidebar UI
        document.querySelectorAll('.nav-item').forEach(item => {
            if (item.dataset.route === path) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // Unmount current
        if (this.currentRoute && this.routes.get(this.currentRoute).unmount) {
            this.routes.get(this.currentRoute).unmount();
        }

        this.currentRoute = path;
        const module = this.routes.get(path);

        // Fade out
        this.mainContent.style.opacity = '0';
        
        // Wait for browser to acknowledge opacity change if CSS transition is present
        await new Promise(r => requestAnimationFrame(r));
        
        // Render new content
        const renderResult = await module.render();
        if (renderResult !== undefined) {
            this.mainContent.innerHTML = renderResult;
        }
        
        // Mount behavior
        if (module.mount) {
            await module.mount();
        }
        
        // Fade in
        this.mainContent.style.opacity = '1';
    }
}

window.router = new Router();
