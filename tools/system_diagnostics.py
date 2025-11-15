"""
System Diagnostic Tool - Custom tool for checking system health.

This tool simulates system diagnostics and demonstrates integration of
custom tools with agents.
"""

from typing import Dict, Any, List
import random


# Simulated system components
SYSTEM_COMPONENTS = {
    "database": {"status": "healthy", "response_time_ms": 45},
    "api_server": {"status": "healthy", "response_time_ms": 120},
    "cache": {"status": "healthy", "response_time_ms": 5},
    "message_queue": {"status": "healthy", "response_time_ms": 15},
    "file_storage": {"status": "healthy", "response_time_ms": 200}
}


def check_system_health(component: str = None) -> Dict[str, Any]:
    """
    Check health of a specific component or all components.
    
    Args:
        component: Name of component to check, or None for all
        
    Returns:
        Health status information
    """
    if component:
        if component not in SYSTEM_COMPONENTS:
            return {"error": f"Component '{component}' not found"}
        return {
            "component": component,
            **SYSTEM_COMPONENTS[component]
        }
    
    # Return all components
    return {
        "components": SYSTEM_COMPONENTS,
        "overall_status": "healthy" if all(c["status"] == "healthy" for c in SYSTEM_COMPONENTS.values()) else "degraded"
    }


def diagnose_issue(symptom: str) -> Dict[str, Any]:
    """
    Diagnose a system issue based on symptoms.
    
    Args:
        symptom: Description of the issue symptom
        
    Returns:
        Diagnostic results with potential causes
    """
    symptom_lower = symptom.lower()
    
    # Simple pattern matching for demonstration
    if "slow" in symptom_lower or "timeout" in symptom_lower:
        return {
            "diagnosis": "Performance degradation",
            "likely_causes": [
                "High database query latency",
                "API server overload",
                "Cache miss rate increase"
            ],
            "recommended_actions": [
                "Check database query performance",
                "Review API server metrics",
                "Investigate cache hit rates"
            ]
        }
    elif "error" in symptom_lower or "failure" in symptom_lower:
        return {
            "diagnosis": "Service failure",
            "likely_causes": [
                "Component crash",
                "Resource exhaustion",
                "Configuration error"
            ],
            "recommended_actions": [
                "Check component logs",
                "Review resource usage",
                "Verify configuration"
            ]
        }
    elif "connection" in symptom_lower:
        return {
            "diagnosis": "Connectivity issue",
            "likely_causes": [
                "Network partition",
                "Service unavailable",
                "Firewall blocking"
            ],
            "recommended_actions": [
                "Check network connectivity",
                "Verify service availability",
                "Review firewall rules"
            ]
        }
    else:
        return {
            "diagnosis": "Unknown issue",
            "likely_causes": ["Requires further investigation"],
            "recommended_actions": [
                "Collect more diagnostic information",
                "Review system logs",
                "Check recent changes"
            ]
        }


def get_system_metrics(component: str) -> Dict[str, Any]:
    """
    Get detailed metrics for a system component.
    
    Args:
        component: Name of component
        
    Returns:
        Metrics data
    """
    if component not in SYSTEM_COMPONENTS:
        return {"error": f"Component '{component}' not found"}
    
    base_metrics = SYSTEM_COMPONENTS[component]
    
    # Simulate additional metrics
    return {
        "component": component,
        "status": base_metrics["status"],
        "response_time_ms": base_metrics["response_time_ms"],
        "cpu_usage_percent": random.randint(20, 80),
        "memory_usage_percent": random.randint(30, 70),
        "request_count": random.randint(1000, 10000),
        "error_rate_percent": random.uniform(0, 2)
    }

