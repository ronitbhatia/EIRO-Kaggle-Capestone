"""
Session Manager for maintaining incident state across agent interactions.

This implements the "Sessions and memory" concept from the course by maintaining
persistent session state that tracks the incident lifecycle and agent decisions.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json


class SessionManager:
    """Manages session state for incident tracking across multiple agents."""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
    
    def create_session(self, incident_id: str, initial_data: Dict[str, Any]) -> None:
        """Create a new session for an incident."""
        self.sessions[incident_id] = {
            "incident_id": incident_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "state": "triage",
            "history": [],
            **initial_data
        }
    
    def get_session(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data for an incident."""
        return self.sessions.get(incident_id)
    
    def update_session(self, incident_id: str, updates: Dict[str, Any]) -> None:
        """Update session data and add to history."""
        if incident_id not in self.sessions:
            raise ValueError(f"Session {incident_id} not found")
        
        self.sessions[incident_id].update(updates)
        self.sessions[incident_id]["updated_at"] = datetime.now().isoformat()
        
        # Add to history for memory
        self.sessions[incident_id]["history"].append({
            "timestamp": datetime.now().isoformat(),
            "updates": updates
        })
    
    def add_to_history(self, incident_id: str, agent: str, action: str, result: Any) -> None:
        """Add an agent action to the session history."""
        if incident_id not in self.sessions:
            raise ValueError(f"Session {incident_id} not found")
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent,
            "action": action,
            "result": result
        }
        self.sessions[incident_id]["history"].append(entry)
    
    def get_history(self, incident_id: str) -> list:
        """Get full history for an incident."""
        if incident_id not in self.sessions:
            return []
        return self.sessions[incident_id].get("history", [])
    
    def set_state(self, incident_id: str, new_state: str) -> None:
        """Update the incident state (triage -> investigation -> resolution -> closed)."""
        self.update_session(incident_id, {"state": new_state})

