from ai.person_tracker import TrackedPerson

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
        
        # 1. Gaze Persistence (how long they've been looking at the screen)
        # Assuming avg_gaze_score > 0.6 means they are looking at the screen
        if person.avg_gaze_score > 0.6:
            if person.persistence_seconds > 10.0:
                score += 0.9
            elif person.persistence_seconds > 5.0:
                score += 0.6
            elif person.persistence_seconds > 2.0:
                score += 0.3
            else:
                score += 0.1
                
        # 2. Approach Pattern (are they getting closer?)
        if len(person.position_history) >= 15:
            # simple check: if bounding box area is increasing over time
            # Since we only have centroid in position_history, we can't easily check area here.
            # But we could check if they moved significantly.
            pass
            
        # Ensure score is within bounds
        return min(max(score, 0.0), 1.0)
