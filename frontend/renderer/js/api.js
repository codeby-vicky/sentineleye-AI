const API_BASE = window.api.getBackendUrl() + '/api';

class ApiService {
    static async request(endpoint, options = {}) {
        const url = `${API_BASE}${endpoint}`;
        try {
            const response = await fetch(url, options);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.message || `HTTP Error ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error(`API Error (${endpoint}):`, error);
            throw error;
        }
    }

    static async get(endpoint) {
        return this.request(endpoint);
    }

    static async post(endpoint, body) {
        return this.request(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        });
    }
    
    static async postForm(endpoint, formData) {
        return this.request(endpoint, {
            method: 'POST',
            body: formData,
        });
    }

    static async put(endpoint, body) {
        return this.request(endpoint, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        });
    }

    static async delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE',
        });
    }
}

window.apiService = ApiService;
