"""
Test suite for the Risk Engine.
Tests threat calculation, behavior analysis, and decision making.
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestThreatCalculator(unittest.TestCase):
    """Tests for the ThreatCalculator."""

    @classmethod
    def setUpClass(cls):
        """Initialize threat calculator."""
        from risk_engine.threat_calculator import ThreatCalculator
        cls.calculator = ThreatCalculator()

    def test_calculator_initialization(self):
        """Test calculator initializes correctly."""
        self.assertIsNotNone(self.calculator)

    def test_owner_only_low_threat(self):
        """Test that owner alone produces LOW threat."""
        from risk_engine.threat_calculator import ObserverData
        observers = [ObserverData(
            identity='Owner',
            identity_type='owner',
            gaze_score=0.9,
            persistence_seconds=100,
            behavior_score=0.0
        )]
        result = self.calculator.calculate(observers, 'safe')
        self.assertEqual(result.level, 'LOW')
        self.assertLessEqual(result.score, 25)

    def test_unknown_observer_high_threat(self):
        """Test unknown observer with gaze produces HIGH threat."""
        from risk_engine.threat_calculator import ObserverData
        observers = [
            ObserverData(
                identity='Owner',
                identity_type='owner',
                gaze_score=0.9,
                persistence_seconds=100,
                behavior_score=0.0
            ),
            ObserverData(
                identity='Unknown',
                identity_type='unknown',
                gaze_score=0.85,
                persistence_seconds=8.0,
                behavior_score=0.7
            )
        ]
        result = self.calculator.calculate(observers, 'confidential')
        self.assertIn(result.level, ['HIGH', 'CRITICAL'])
        self.assertGreater(result.score, 50)

    def test_trusted_person_reduced_threat(self):
        """Test trusted person gets reduced threat score."""
        from risk_engine.threat_calculator import ObserverData
        observers = [
            ObserverData(
                identity='Owner',
                identity_type='owner',
                gaze_score=0.9,
                persistence_seconds=100,
                behavior_score=0.0
            ),
            ObserverData(
                identity='Friend1',
                identity_type='trusted',
                gaze_score=0.8,
                persistence_seconds=5.0,
                behavior_score=0.2
            )
        ]
        result = self.calculator.calculate(observers, 'personal')
        self.assertIn(result.level, ['LOW', 'MEDIUM'])

    def test_crossing_minimal_threat(self):
        """Test crossing person gets minimal threat score."""
        from risk_engine.threat_calculator import ObserverData
        observers = [
            ObserverData(
                identity='Owner',
                identity_type='owner',
                gaze_score=0.9,
                persistence_seconds=100,
                behavior_score=0.0
            ),
            ObserverData(
                identity='Crossing',
                identity_type='crossing',
                gaze_score=0.1,
                persistence_seconds=1.5,
                behavior_score=0.0
            )
        ]
        result = self.calculator.calculate(observers, 'confidential')
        self.assertEqual(result.level, 'LOW')

    def test_threat_score_range(self):
        """Test that threat score is always in 0-100 range."""
        from risk_engine.threat_calculator import ObserverData
        observers = [ObserverData(
            identity='Unknown',
            identity_type='unknown',
            gaze_score=1.0,
            persistence_seconds=60,
            behavior_score=1.0
        )]
        result = self.calculator.calculate(observers, 'highly_confidential')
        self.assertGreaterEqual(result.score, 0)
        self.assertLessEqual(result.score, 100)


class TestDecisionEngine(unittest.TestCase):
    """Tests for the DecisionEngine."""

    @classmethod
    def setUpClass(cls):
        """Initialize decision engine."""
        from risk_engine.decision_engine import DecisionEngine
        cls.engine = DecisionEngine()

    def test_low_threat_popup_only(self):
        """Test LOW threat produces only popup action."""
        from risk_engine.threat_calculator import ThreatResult
        threat = ThreatResult(score=15, level='LOW', reason='test', contributing_factors=[])
        actions = self.engine.decide(threat)
        action_types = [a.action_type for a in actions]
        self.assertIn('popup', action_types)
        self.assertNotIn('lock', action_types)
        self.assertNotIn('blur', action_types)

    def test_critical_threat_full_defense(self):
        """Test CRITICAL threat activates all defenses."""
        from risk_engine.threat_calculator import ThreatResult
        threat = ThreatResult(score=85, level='CRITICAL', reason='test', contributing_factors=[])
        actions = self.engine.decide(threat)
        action_types = [a.action_type for a in actions]
        self.assertIn('popup', action_types)
        self.assertIn('blur', action_types)
        self.assertIn('lock', action_types)
        self.assertIn('autosave', action_types)


if __name__ == '__main__':
    unittest.main()
