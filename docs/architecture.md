# SentinelEye AI — Architecture Documentation

## System Architecture

SentinelEye AI is a modular, multimodal desktop application that combines Computer Vision and Natural Language Processing to prevent shoulder surfing attacks.

## Architecture Layers

### 1. Presentation Layer (Electron.js)
- **Custom dark-themed UI** with glassmorphism design
- **7 pages**: Setup, Trusted Users, Monitoring, Dashboard, Logs, Analytics, Settings
- **Real-time updates** via WebSocket (Socket.IO)
- **Chart.js** for data visualization
- **Notification system** with sound alerts

### 2. API Layer (Flask)
- **REST API** for CRUD operations
- **WebSocket** for real-time event streaming
- **Blueprints** for modular route organization
- **CORS** enabled for Electron communication

### 3. Service Layer
- **AuthService**: Owner registration and verification
- **UserService**: Trusted user management
- **MonitoringService**: Core orchestrator — coordinates all AI modules
- **DefenseService**: Executes privacy defense actions

### 4. AI Inference Layer
- **FaceDetector** (MediaPipe): Multi-face detection at 30+ FPS
- **FaceRecognizer** (face_recognition): 128-D embedding-based identity verification
- **GazeEstimator** (MediaPipe Face Mesh): Head pose + iris-based gaze scoring
- **MotionDetector** (OpenCV MOG2): Crossing person detection
- **PersonTracker**: Centroid-based multi-person tracking with persistence tracking

### 5. Content Analysis Layer
- **ScreenCapture** (mss): Periodic screen content capture
- **TextExtractor** (EasyOCR): GPU-accelerated text extraction
- **SensitivityClassifier** (sentence-transformers): Semantic content classification
- **ContextAnalyzer**: Document type and information density analysis

### 6. Intelligence Layer
- **ThreatCalculator**: Weighted multi-factor risk scoring
- **BehaviorAnalyzer**: Temporal behavior pattern analysis
- **DecisionEngine**: Maps threat levels to defense actions

### 7. Defense Layer
- **ScreenBlur**: Transparent overlay via Electron
- **WindowManager**: OS-level window management (ctypes)
- **WorkstationLock**: Windows lock via Win32 API
- **AlertManager**: Notification dispatch with sound support

### 8. Storage Layer
- **SQLite** with WAL mode for concurrent access
- **6 tables**: owner, trusted_user, detection_event, session, settings, alert_log
- **Binary embedding storage** for face recognition

## Data Flow

```
Camera Frame (30fps)
    ↓
Face Detection (MediaPipe)
    ↓
┌─── For each face ───┐
│  Face Recognition    │
│  Gaze Estimation     │
│  Person Tracking     │
└──────────────────────┘
    ↓
Screen Capture (every 5s)
    ↓
OCR → NLP Classification
    ↓
Risk Calculation (all factors combined)
    ↓
Defense Decision
    ↓
Action Execution + Event Logging + WebSocket Notification
```

## Communication Protocol

- **HTTP REST**: Settings, user management, event queries
- **WebSocket**: Real-time threat alerts, camera feed, defense triggers
- **IPC (Electron)**: OS-level actions (lock, blur overlay, sound)
