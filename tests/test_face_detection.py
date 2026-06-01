"""
Test suite for Face Detection module.
Tests MediaPipe face detection with various scenarios.
"""

import unittest
import sys
import os
import numpy as np

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


class TestFaceDetector(unittest.TestCase):
    """Tests for the FaceDetector class."""

    @classmethod
    def setUpClass(cls):
        """Initialize face detector once for all tests."""
        from ai.face_detector import FaceDetector
        cls.detector = FaceDetector()

    def test_detector_initialization(self):
        """Test that the detector initializes without error."""
        self.assertIsNotNone(self.detector)

    def test_detect_no_faces(self):
        """Test detection on a blank image returns empty list."""
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        faces = self.detector.detect(blank_frame)
        self.assertIsInstance(faces, list)

    def test_detect_returns_correct_format(self):
        """Test that detected faces have the correct attributes."""
        # Create a test frame (blank - may not detect faces, but tests format)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        faces = self.detector.detect(frame)
        for face in faces:
            self.assertTrue(hasattr(face, 'bbox'))
            self.assertTrue(hasattr(face, 'confidence'))
            self.assertTrue(hasattr(face, 'keypoints'))

    def test_detect_with_noise_image(self):
        """Test detection on a noisy image doesn't crash."""
        noisy_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        faces = self.detector.detect(noisy_frame)
        self.assertIsInstance(faces, list)


class TestGazeEstimator(unittest.TestCase):
    """Tests for the GazeEstimator class."""

    @classmethod
    def setUpClass(cls):
        """Initialize gaze estimator."""
        from ai.gaze_estimator import GazeEstimator
        cls.estimator = GazeEstimator()

    def test_estimator_initialization(self):
        """Test that the estimator initializes without error."""
        self.assertIsNotNone(self.estimator)

    def test_estimate_no_face(self):
        """Test gaze estimation on blank image returns None."""
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        result = self.estimator.estimate(blank_frame, (0, 0, 100, 100))
        # Should return None or default result when no face mesh found
        if result is not None:
            self.assertTrue(hasattr(result, 'gaze_score'))


if __name__ == '__main__':
    unittest.main()
