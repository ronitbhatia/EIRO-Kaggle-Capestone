"""
Notification Tool - Custom tool for sending alerts and updates.

This tool demonstrates how agents can communicate with stakeholders
through notifications.
"""

from typing import Dict, Any, List
from datetime import datetime


class NotificationService:
    """Service for managing and sending notifications."""
    
    def __init__(self):
        self.notifications: List[Dict[str, Any]] = []
    
    def send_notification(self, recipient: str, subject: str, message: str, 
                         priority: str = "normal") -> Dict[str, Any]:
        """
        Send a notification.
        
        Args:
            recipient: Email or user ID
            subject: Notification subject
            message: Notification message
            priority: Priority level (low, normal, high, urgent)
            
        Returns:
            Notification record
        """
        notification = {
            "id": f"NOTIF-{len(self.notifications) + 1:04d}",
            "recipient": recipient,
            "subject": subject,
            "message": message,
            "priority": priority,
            "status": "sent",
            "sent_at": datetime.now().isoformat()
        }
        
        self.notifications.append(notification)
        
        # In a real system, this would send email/Slack/etc.
        print(f"\nNOTIFICATION [{priority.upper()}]")
        print(f"To: {recipient}")
        print(f"Subject: {subject}")
        print(f"Message: {message}\n")
        
        return notification
    
    def get_notifications(self, recipient: str = None) -> List[Dict[str, Any]]:
        """Get notifications, optionally filtered by recipient."""
        if recipient:
            return [n for n in self.notifications if n["recipient"] == recipient]
        return self.notifications


# Global instance
notification_service = NotificationService()


def send_notification_tool(recipient: str, subject: str, message: str, 
                           priority: str = "normal") -> Dict[str, Any]:
    """Tool function for sending notifications."""
    return notification_service.send_notification(recipient, subject, message, priority)

