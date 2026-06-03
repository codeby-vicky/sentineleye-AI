from ai.person_tracker import TrackedPerson
import numpy as np

class BehaviorAnalyzer:
    def __init__(self):
        pass
        
    def analyze(self, person: TrackedPerson) -> float:
        """
        Analyze behavior of a tracked person and return a behavior anomaly score (0.0 to 1.0).
        """
        if person.identity_type == 'owner':
            return 0.0
            
        score = 0.0
        
        # 1. Gaze Persistence
        if person.avg_gaze_score > 0.6:
            if person.persistence_seconds > 10.0:
                score += 0.9
            elif person.persistence_seconds > 5.0:
                score += 0.6
            elif person.persistence_seconds > 2.0:
                score += 0.3
            else:
                score += 0.1
                
        # 2. Approach Pattern (face getting bigger = getting closer)
        if person.is_approaching:
            score += 0.3
            
        # 3. Lateral movement analysis
        if len(person.position_history) >= 10:
            positions = person.position_history[-10:]
            x_positions = [p[0] for p in positions]
            x_range = max(x_positions) - min(x_positions)
            y_positions = [p[1] for p in positions]
            y_range = max(y_positions) - min(y_positions)
            
            # Standing still (low movement) while looking = suspicious
            if x_range < 30 and y_range < 30 and person.avg_gaze_score > 0.4:
                score += 0.2  # Stationary observer
            
            # Large lateral movement = crossing
            if x_range > 200 and person.persistence_seconds < 3.0:
                score -= 0.2  # Likely crossing, reduce score
                
        # Ensure score is within bounds
        return min(max(score, 0.0), 1.0)
