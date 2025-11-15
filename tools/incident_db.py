"""
Incident Database Tool - Custom tool for managing incident records.

This is a custom tool that demonstrates the "Tools" concept from the course.
It provides CRUD operations for incident management.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


class IncidentDatabase:
    """In-memory database for incident management."""
    
    def __init__(self):
        self.incidents: Dict[str, Dict[str, Any]] = {}
        self.next_id = 1
    
    def create_incident(self, title: str, description: str, reporter: str, 
                       severity: str = "medium") -> Dict[str, Any]:
        """Create a new incident record."""
        incident_id = f"INC-{self.next_id:04d}"
        self.next_id += 1
        
        incident = {
            "id": incident_id,
            "title": title,
            "description": description,
            "reporter": reporter,
            "severity": severity,
            "status": "open",
            "priority": None,
            "category": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "assigned_agent": None,
            "resolution": None
        }
        
        self.incidents[incident_id] = incident
        return incident
    
    def get_incident(self, incident_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve an incident by ID."""
        return self.incidents.get(incident_id)
    
    def update_incident(self, incident_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update incident fields."""
        if incident_id not in self.incidents:
            return None
        
        self.incidents[incident_id].update(updates)
        self.incidents[incident_id]["updated_at"] = datetime.now().isoformat()
        return self.incidents[incident_id]
    
    def list_incidents(self, status: Optional[str] = None, 
                      severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """List incidents with optional filtering."""
        results = list(self.incidents.values())
        
        if status:
            results = [inc for inc in results if inc["status"] == status]
        if severity:
            results = [inc for inc in results if inc["severity"] == severity]
        
        return results
    
    def close_incident(self, incident_id: str, resolution: str) -> Optional[Dict[str, Any]]:
        """Close an incident with a resolution."""
        return self.update_incident(incident_id, {
            "status": "closed",
            "resolution": resolution
        })


# Global instance
incident_db = IncidentDatabase()


def create_incident_tool(title: str, description: str, reporter: str, severity: str = "medium") -> Dict[str, Any]:
    """Tool function for creating incidents."""
    return incident_db.create_incident(title, description, reporter, severity)


def get_incident_tool(incident_id: str) -> Optional[Dict[str, Any]]:
    """Tool function for retrieving incidents."""
    return incident_db.get_incident(incident_id)


def update_incident_tool(incident_id: str, **updates) -> Optional[Dict[str, Any]]:
    """Tool function for updating incidents."""
    return incident_db.update_incident(incident_id, updates)


def list_incidents_tool(status: Optional[str] = None, severity: Optional[str] = None) -> List[Dict[str, Any]]:
    """Tool function for listing incidents."""
    return incident_db.list_incidents(status, severity)

