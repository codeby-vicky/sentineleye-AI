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
        
    def decide(self, threat: ThreatResult, screen_sensitivity: str = 'safe') -> List[DefenseAction]:
        """
        Decide which defense actions to take based on the threat result and user settings.
        """
        actions = []
        settings = db.get_all_settings()
        
        level = threat.level
        
        if level == 'LOW':
            if settings.get('defense_low_popup', 'true') == 'true':
                actions.append(DefenseAction('popup', {'message': "Observer crossed behind (ignored)", 'level': level}))
                
        elif level == 'MEDIUM':
            intensity = 'full' if screen_sensitivity in ['confidential', 'highly_confidential'] else 'partial'
            if settings.get('defense_medium_blur', 'true') == 'true':
                actions.append(DefenseAction('blur', {'intensity': intensity}))
            if settings.get('defense_medium_autosave', 'true') == 'true':
                actions.append(DefenseAction('autosave', {}))
            actions.append(DefenseAction('popup', {'message': "Suspicious observer detected. Privacy blur activated.", 'level': level}))
            
        elif level == 'HIGH':
            if settings.get('defense_medium_blur', 'true') == 'true':
                actions.append(DefenseAction('blur', {'intensity': 'full'}))
            if settings.get('defense_high_autosave', 'true') == 'true':
                actions.append(DefenseAction('autosave', {}))
            actions.append(DefenseAction('popup', {'message': "Unknown person standing behind. Privacy protection enabled.", 'level': level}))
            
        elif level == 'CRITICAL':
            if settings.get('defense_critical_lock', 'true') == 'true':
                actions.append(DefenseAction('lock', {}))
            else:
                actions.append(DefenseAction('blur', {'intensity': 'full'}))
            actions.append(DefenseAction('popup', {'message': "Critical threat: Screen watching or recording on sensitive content. Blur fully active.", 'level': level}))
            
        return actions
