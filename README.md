# 🛡️ SentinelEye AI

## Intelligent Shoulder Surfing Prevention System using Computer Vision & NLP

> A production-grade, multimodal AI-powered privacy guardian that protects sensitive on-screen information from unauthorized visual observation.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11+-green)
![Electron](https://img.shields.io/badge/electron-31.x-purple)
![License](https://img.shields.io/badge/license-MIT-yellow)

---

## 📋 Overview

SentinelEye AI is a desktop application that uses **computer vision**, **face recognition**, **gaze estimation**, and **NLP-based content analysis** to detect and prevent shoulder surfing attacks in real-time.

### Core Capabilities

| Feature | Description |
|---------|-------------|
| 🔐 **Owner Authentication** | Register and verify device owner via face recognition |
| 👥 **Trusted User Management** | Register trusted people with configurable trust levels |
| 👁️ **Gaze Estimation** | Detect if observers are looking at your screen |
| 🚶 **Crossing Detection** | Distinguish passing people from persistent observers |
| 📝 **Screen Analysis (OCR + NLP)** | Semantically classify on-screen content sensitivity |
| ⚠️ **Risk Intelligence** | Multi-factor threat scoring combining all signals |
| 🛡️ **Privacy Defense** | Automated screen blur, window minimize, workstation lock |
| 📊 **Analytics Dashboard** | Real-time monitoring and historical threat analytics |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                 Electron Frontend                    │
│  ┌──────────┐ ┌──────────┐ ┌────────────────────┐  │
│  │ Dashboard │ │ Monitor  │ │ Settings/Analytics │  │
│  └──────────┘ └──────────┘ └────────────────────┘  │
│                    │ HTTP + WebSocket                │
├────────────────────┼────────────────────────────────┤
│              Flask Backend (Python)                  │
│  ┌─────────┐ ┌──────────┐ ┌──────────────────┐     │
│  │ REST API │ │ SocketIO │ │ Services Layer   │     │
│  └─────────┘ └──────────┘ └──────────────────┘     │
│                    │                                 │
│  ┌─────────────────┼─────────────────────────┐      │
│  │           AI Inference Engine              │      │
│  │  MediaPipe │ face_recognition │ OpenCV     │      │
│  │  EasyOCR   │ sentence-transformers        │      │
│  └────────────────────────────────────────────┘     │
│                    │                                 │
│  ┌─────────────────┼──────────────────┐             │
│  │    Risk Engine   │  Defense Engine  │             │
│  └──────────────────┴──────────────────┘             │
│                    │                                 │
│  ┌─────────────────────────────────────┐             │
│  │          SQLite Database            │             │
│  └─────────────────────────────────────┘             │
└─────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Electron.js 31.x |
| Backend | Python 3.11+ / Flask 3.x |
| Face Detection | MediaPipe Face Landmarker |
| Face Recognition | face_recognition (dlib) |
| Gaze Estimation | MediaPipe Face Mesh + solvePnP |
| OCR | EasyOCR (CUDA) |
| NLP | sentence-transformers (all-MiniLM-L6-v2) |
| Screen Capture | mss |
| Database | SQLite3 (WAL mode) |
| Real-time | Flask-SocketIO |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** installed
- **Node.js 18+** installed
- **NVIDIA GPU** with CUDA (optional, for GPU acceleration)
- **Windows 10/11**

### Installation

#### 1. Clone the repository

```bash
git clone <repository-url>
cd sentineleye-ai
```

#### 2. Set up Python backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

#### 3. Set up Electron frontend

```bash
cd frontend
npm install
```

#### 4. Run the application

```bash
cd frontend
npm start
```

The Electron app will automatically start the Flask backend.

### Manual Development Mode

**Terminal 1 — Backend:**
```bash
cd backend
python run.py
```

**Terminal 2 — Frontend:**
```bash
cd frontend
npm run dev
```

---

## 📁 Project Structure

```
sentineleye-ai/
├── frontend/               # Electron desktop app
│   ├── main.js             # Main process
│   ├── preload.js          # Context bridge
│   └── renderer/           # UI (HTML/CSS/JS)
│       ├── index.html      # App shell
│       ├── css/            # Design system & styles
│       └── js/             # Application logic & pages
│
├── backend/                # Python Flask backend
│   ├── app.py              # Flask application factory
│   ├── run.py              # Entry point
│   ├── api/                # REST API routes
│   ├── services/           # Business logic
│   ├── ai/                 # CV modules (detection, recognition, gaze)
│   ├── ocr/                # Screen capture & OCR
│   ├── nlp/                # Sensitivity classification
│   ├── risk_engine/        # Threat scoring
│   ├── defense/            # Privacy actions
│   ├── database/           # SQLite layer
│   └── utils/              # Helpers & utilities
│
├── models/                 # Pre-trained model weights
├── tests/                  # Test suite
├── docs/                   # Documentation
└── scripts/                # Setup scripts
```

---

## ⚙️ Configuration

All settings are configurable through the Settings page in the app. Key parameters:

| Setting | Default | Description |
|---------|---------|-------------|
| Camera Resolution | 1080p | Webcam capture resolution |
| Face Recognition Threshold | 0.6 | Euclidean distance for face match |
| Gaze Yaw Threshold | 15° | Max yaw angle for screen gaze |
| OCR Interval | 5s | Screen analysis frequency |
| Crossing Max Duration | 3s | Max duration for crossing classification |
| Sound Alerts | Enabled | Audio notifications |

---

## 📊 Risk Scoring

Threat score is calculated using weighted multi-factor analysis:

| Factor | Weight |
|--------|--------|
| Observer Identity | 25% |
| Screen Gaze | 20% |
| Persistence | 15% |
| Screen Sensitivity | 20% |
| Observer Count | 10% |
| Behavior Anomaly | 10% |

**Threat Levels:**
- 🟢 **LOW** (0-25): Popup notification
- 🟡 **MEDIUM** (26-50): Screen blur + autosave
- 🟠 **HIGH** (51-75): Minimize + blur + autosave
- 🔴 **CRITICAL** (76-100): Lock workstation

---

## 📜 License

MIT License — See [LICENSE](LICENSE) for details.

---

## 👤 Author

Final Year Project — SentinelEye AI

---

*Built with ❤️ using Computer Vision, NLP, and Electron.js*
