from dataclasses import dataclass
from typing import List, Dict
from config import Config

@dataclass
class ObserverData:
    identity: str
    identity_type: str  # 'owner', 'trusted', 'unknown', 'crossing'
    gaze_score: float
    persistence_seconds: float
    behavior_score: float

@dataclass
class ThreatResult:
    score: float
    level: str
    reason: str
    contributing_factors: List[str]

class ThreatCalculator:
    def __init__(self):
        self.weights = Config.THREAT_WEIGHTS
        self.thresholds = Config.THREAT_LEVEL_THRESHOLDS
        
    def calculate(self, observers: List[ObserverData], screen_sensitivity: str, window_title: str = "") -> ThreatResult:
        """
        Calculate overall threat score based on observers and screen content.
        Returns score (0-100) and threat level.
        """
        if not observers:
            return ThreatResult(0.0, 'LOW', "No observers", [])
            
        factors = []
        
        # Base factor: Screen Sensitivity
        sensitivity_scores = {
            'safe': 0.0,
            'personal': 0.4,
            'confidential': 0.7,
            'highly_confidential': 1.0
        }
        sens_score = sensitivity_scores.get(screen_sensitivity, 0.0)
        
        from database.db import db
        settings = db.get_all_settings()
        privacy_mode = settings.get('privacy_sensitivity', 'medium')
        
        # Adjust screen sensitivity score based on privacy mode
        if privacy_mode == 'aggressive':
            sens_score = max(sens_score + 0.3, 1.0)
        elif privacy_mode == 'low':
            sens_score = max(sens_score - 0.2, 0.0)
            
        # Calculate max threat from all observers
        max_observer_threat = 0.0
        primary_reason = ""
        
        for obs in observers:
            # Identity Score
            identity_scores = {'owner': 0.0, 'unknown': 1.0, 'crossing': 1.0}
            id_score = identity_scores.get(obs.identity_type, 1.0)
            
            # Gaze Score (already 0.0 to 1.0)
            g_score = obs.gaze_score
            
            # Persistence Score (normalize to 1.0 at 30 seconds)
            p_score = min(obs.persistence_seconds / 30.0, 1.0)
            
            # Weighted sum for this observer
            obs_threat = (
                self.weights['observer_identity'] * id_score +
                self.weights['gaze_toward_screen'] * g_score +
                self.weights['persistence_duration'] * p_score +
                self.weights['behavior_anomaly'] * obs.behavior_score +
                self.weights['screen_sensitivity'] * sens_score
            )
            
            # Multipliers
            if obs.identity_type == 'crossing':
                obs_threat *= Config.CROSSING_DISCOUNT
            elif obs.identity_type == 'owner':
                obs_threat = 0.0  # Owner is never a threat
                
            if obs_threat > max_observer_threat:
                max_observer_threat = obs_threat
                primary_reason = f"{obs.identity_type.capitalize()} observer + {screen_sensitivity} content"
                if g_score > 0.6:
                    primary_reason += " + sustained gaze"
                    
        # Apply multi-observer multiplier
        observer_count = len([o for o in observers if o.identity_type != 'owner'])
        if observer_count > 1:
            multiplier = 1.0 + 0.2 * (observer_count - 1)
            max_observer_threat *= multiplier
            factors.append(f"Multiple observers ({observer_count})")
            
        # Final score scaling
        final_score = min(max_observer_threat * 100.0, 100.0)
        
        # Smart Privacy Blur Logic
        for obs in observers:
            if obs.identity_type == 'unknown':
                # Check for strict blur triggers
                facing_screen = obs.gaze_score > 0.6
                standing_long_enough = obs.persistence_seconds > 2.0
                
                is_sensitive = (screen_sensitivity in ['confidential', 'highly_confidential'])
                if privacy_mode == 'aggressive':
                    is_sensitive = True
                elif privacy_mode == 'low':
                    is_sensitive = (screen_sensitivity == 'highly_confidential')
                
                if facing_screen and standing_long_enough and is_sensitive:
                    final_score = max(final_score, self.thresholds['CRITICAL'])
                    primary_reason = f"Screen Watching on Sensitive Content ({screen_sensitivity})"
                elif facing_screen:
                    final_score = max(final_score, self.thresholds['HIGH'])
                    primary_reason = "Unknown Person Facing Monitor"
                elif standing_long_enough:
                    final_score = max(final_score, self.thresholds['MEDIUM'])
                    primary_reason = "Unknown Person Standing Behind"
            elif obs.identity_type == 'crossing':
                if final_score < self.thresholds['LOW'] + 5:
                    final_score = max(final_score, 10.0)
                    primary_reason = "Observer Crossing Detected"
        
        # Determine Level
        level = 'LOW'
        if final_score >= self.thresholds['CRITICAL']:
            level = 'CRITICAL'
        elif final_score >= self.thresholds['HIGH']:
            level = 'HIGH'
        elif final_score >= self.thresholds['MEDIUM']:
            level = 'MEDIUM'
            
        if final_score == 0.0:
            primary_reason = "Safe"
            
        return ThreatResult(
            score=round(final_score, 1),
            level=level,
            reason=primary_reason,
            contributing_factors=factors
        )
