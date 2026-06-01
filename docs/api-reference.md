# SentinelEye AI — API Reference

## Base URL

```
http://localhost:5000
```

## Authentication & Owner

### Register Owner
```http
POST /api/auth/register-owner
Content-Type: multipart/form-data

Body:
  name: string (owner name)
  images: File[] (5 face images at different angles)

Response: 200
{
  "success": true,
  "message": "Owner registered successfully",
  "owner_id": 1
}
```

### Verify Owner
```http
POST /api/auth/verify-owner
Content-Type: application/json

Body:
{
  "image": "<base64-encoded-image>"
}

Response: 200
{
  "verified": true,
  "confidence": 0.85,
  "name": "Vicky"
}
```

### Get Owner Profile
```http
GET /api/auth/owner

Response: 200
{
  "id": 1,
  "name": "Vicky",
  "created_at": "2026-05-24T10:30:00Z",
  "is_active": true
}
```

---

## Trusted Users

### List Trusted Users
```http
GET /api/users/trusted

Response: 200
{
  "users": [
    {
      "id": 1,
      "name": "Friend1",
      "relationship": "friend",
      "trust_level": 0.8,
      "created_at": "2026-05-24T11:00:00Z",
      "is_active": true
    }
  ]
}
```

### Add Trusted User
```http
POST /api/users/trusted
Content-Type: multipart/form-data

Body:
  name: string
  relationship: "friend" | "colleague" | "family"
  images: File[] (3 face images)

Response: 201
{
  "success": true,
  "user_id": 1,
  "message": "Trusted user added"
}
```

### Update Trusted User
```http
PUT /api/users/trusted/:id
Content-Type: application/json

Body:
{
  "trust_level": 0.9,
  "relationship": "family"
}

Response: 200
{
  "success": true,
  "message": "User updated"
}
```

### Delete Trusted User
```http
DELETE /api/users/trusted/:id

Response: 200
{
  "success": true,
  "message": "User removed"
}
```

---

## Monitoring

### Start Monitoring
```http
POST /api/monitoring/start

Response: 200
{
  "success": true,
  "session_id": 1,
  "message": "Monitoring started"
}
```

### Stop Monitoring
```http
POST /api/monitoring/stop

Response: 200
{
  "success": true,
  "session_id": 1,
  "message": "Monitoring stopped",
  "session_summary": {
    "duration": "01:23:45",
    "total_detections": 47,
    "unknown_count": 3,
    "high_risk_count": 1
  }
}
```

### Get Monitoring Status
```http
GET /api/monitoring/status

Response: 200
{
  "active": true,
  "session_id": 1,
  "session_duration": "00:15:32",
  "current_threat_score": 12.5,
  "current_threat_level": "LOW",
  "faces_detected": 1,
  "screen_sensitivity": "safe"
}
```

### Get Camera Feed Frame
```http
GET /api/monitoring/feed

Response: 200
{
  "frame": "<base64-encoded-annotated-frame>",
  "detections": [
    {
      "identity": "Vicky",
      "type": "owner",
      "bbox": [100, 50, 200, 250],
      "gaze_score": 0.9,
      "gaze_direction": "toward_screen"
    }
  ],
  "threat_score": 12.5,
  "threat_level": "LOW"
}
```

---

## Events & Logs

### Get Events
```http
GET /api/events?page=1&per_page=20&observer_type=unknown&threat_level=HIGH&date_from=2026-05-24&date_to=2026-05-24

Response: 200
{
  "events": [...],
  "total": 150,
  "page": 1,
  "per_page": 20,
  "pages": 8
}
```

### Get Single Event
```http
GET /api/events/:id

Response: 200
{
  "id": 42,
  "timestamp": "2026-05-24T14:32:15Z",
  "observer_type": "unknown",
  "observer_name": "Unknown #3",
  "gaze_score": 0.87,
  "persistence_seconds": 7.2,
  "screen_sensitivity": "confidential",
  "threat_score": 72.5,
  "threat_level": "HIGH",
  "action_taken": "blur,minimize",
  "reason": "Unknown observer + confidential content + sustained gaze"
}
```

### Export Events CSV
```http
GET /api/events/export?date_from=2026-05-01&date_to=2026-05-24

Response: 200 (text/csv)
```

---

## Analytics

### Summary Statistics
```http
GET /api/analytics/summary

Response: 200
{
  "today": {
    "total_detections": 47,
    "threats_blocked": 5,
    "unknown_observers": 3,
    "crossing_events": 12,
    "high_risk_incidents": 1,
    "avg_threat_score": 18.5,
    "protected_hours": 6.5
  },
  "all_time": {
    "total_detections": 1250,
    "total_sessions": 45
  }
}
```

### Threat Timeline
```http
GET /api/analytics/timeline?period=24h

Response: 200
{
  "labels": ["10:00", "10:15", "10:30", ...],
  "scores": [12.5, 8.0, 45.2, ...]
}
```

### Distribution
```http
GET /api/analytics/distribution

Response: 200
{
  "by_observer_type": {
    "owner": 500,
    "trusted": 300,
    "unknown": 100,
    "crossing": 350
  },
  "by_threat_level": {
    "LOW": 900,
    "MEDIUM": 250,
    "HIGH": 80,
    "CRITICAL": 20
  }
}
```

---

## Settings

### Get Settings
```http
GET /api/settings

Response: 200
{
  "settings": {
    "camera_index": "0",
    "gaze_threshold": "15",
    "persistence_threshold": "5",
    "ocr_interval": "5",
    "sound_enabled": "true",
    "defense_low_popup": "true",
    "defense_medium_blur": "true",
    ...
  }
}
```

### Update Settings
```http
PUT /api/settings
Content-Type: application/json

Body:
{
  "gaze_threshold": "20",
  "sound_enabled": "false"
}

Response: 200
{
  "success": true,
  "message": "Settings updated"
}
```

---

## WebSocket Events

### Server → Client

| Event | Payload | Description |
|-------|---------|-------------|
| `threat_detected` | `{threat_score, level, observer, reason, timestamp}` | New threat detected |
| `frame_update` | `{frame, detections, threat_score, threat_level}` | Camera frame update |
| `status_update` | `{active, session_stats}` | Monitoring status change |
| `crossing_detected` | `{timestamp, duration, message}` | Someone passed behind |
| `defense_activated` | `{action, reason, threat_level}` | Defense action triggered |

### Client → Server

| Event | Payload | Description |
|-------|---------|-------------|
| `acknowledge_alert` | `{alert_id}` | User acknowledged alert |
