from dataclasses import dataclass
from typing import List, Dict
from risk_engine.threat_calculator import ThreatResult
from database.db import db

@dataclass
class DefenseAction:
    action_type: str  # 'popup', 'blur', 'minimize', 'lock', 'autosave'
    parameters: dict

class DecisionEngine:
    def __init__(self):
        pass
        
    def decide(self, threat: ThreatResult) -> List[DefenseAction]:
        """
        Decide which defense actions to take based on the threat result and user settings.
        Graduated response:
          LOW = notification only (quick crossing)
          MEDIUM = partial blur + notification (person standing behind)
          HIGH = full blur + notification (sustained presence)
          CRITICAL = full blur + lock option (phone recording risk)
        """
        actions = []
        settings = db.get_all_settings()
        
        level = threat.level
        
        if level == 'LOW':
            # Level 1: Quick crossing - notification only, no blur
            actions.append(DefenseAction('popup', {'message': threat.reason, 'level': level}))
                
        elif level == 'MEDIUM':
            # Level 2: Person remains behind owner - partial blur
            if settings.get('defense_medium_blur', 'true') == 'true':
                actions.append(DefenseAction('blur', {'intensity': 'partial'}))
            actions.append(DefenseAction('popup', {'message': threat.reason, 'level': level}))
            
        elif level == 'HIGH':
            # Level 3: Sustained presence - full blur
            actions.append(DefenseAction('blur', {'intensity': 'full'}))
            if settings.get('defense_high_autosave', 'true') == 'true':
                actions.append(DefenseAction('autosave', {}))
            actions.append(DefenseAction('popup', {'message': threat.reason, 'level': level}))
            
        elif level == 'CRITICAL':
            # Level 4: Phone recording risk - maximum protection
            if settings.get('defense_critical_lock', 'true') == 'true':
                actions.append(DefenseAction('lock', {}))
            actions.append(DefenseAction('blur', {'intensity': 'full'}))
            actions.append(DefenseAction('popup', {'message': threat.reason, 'level': level}))
            
        return actions
