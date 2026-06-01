"""
Test suite for Flask API endpoints.
Tests all REST API routes.
"""

import unittest
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestAPIBase(unittest.TestCase):
    """Base class for API tests."""

    @classmethod
    def setUpClass(cls):
        """Create test Flask app."""
        from app import create_app
        cls.app = create_app(testing=True)
        cls.client = cls.app.test_client()
        cls.app.testing = True


class TestHealthEndpoint(TestAPIBase):
    """Test health check endpoint."""

    def test_health_check(self):
        """Test /api/health returns 200."""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')


class TestAuthRoutes(TestAPIBase):
    """Test authentication routes."""

    def test_get_owner_no_owner(self):
        """Test getting owner when none registered."""
        response = self.client.get('/api/auth/owner')
        self.assertIn(response.status_code, [200, 404])

    def test_verify_owner_no_image(self):
        """Test verify without image returns error."""
        response = self.client.post('/api/auth/verify-owner',
                                     content_type='application/json',
                                     data=json.dumps({}))
        self.assertIn(response.status_code, [400, 422])


class TestUserRoutes(TestAPIBase):
    """Test trusted user routes."""

    def test_get_trusted_users_empty(self):
        """Test getting trusted users when none registered."""
        response = self.client.get('/api/users/trusted')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('users', data)


class TestMonitoringRoutes(TestAPIBase):
    """Test monitoring routes."""

    def test_get_status(self):
        """Test monitoring status endpoint."""
        response = self.client.get('/api/monitoring/status')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('active', data)


class TestSettingsRoutes(TestAPIBase):
    """Test settings routes."""

    def test_get_settings(self):
        """Test getting all settings."""
        response = self.client.get('/api/settings')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('settings', data)


class TestAnalyticsRoutes(TestAPIBase):
    """Test analytics routes."""

    def test_get_summary(self):
        """Test analytics summary endpoint."""
        response = self.client.get('/api/analytics/summary')
        self.assertEqual(response.status_code, 200)


class TestEventRoutes(TestAPIBase):
    """Test event log routes."""

    def test_get_events_empty(self):
        """Test getting events when none exist."""
        response = self.client.get('/api/events')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('events', data)


if __name__ == '__main__':
    unittest.main()
