"""
Observability module for logging, tracing, and metrics.

This implements the "Observability" concept from the course by providing
structured logging and trace tracking across agent interactions.
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json


class ObservabilityLogger:
    """Structured logging and tracing for agent operations."""
    
    def __init__(self):
        self.logs: list = []
        self.traces: Dict[str, list] = {}
        self.metrics: Dict[str, Any] = {
            "agent_calls": 0,
            "tool_calls": 0,
            "errors": 0
        }
    
    def log(self, level: str, agent: str, message: str, context: Optional[Dict[str, Any]] = None) -> None:
        """Log an event with structured data."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "agent": agent,
            "message": message,
            "context": context or {}
        }
        self.logs.append(log_entry)
        
        # Print for immediate visibility (in Kaggle notebook)
        print(f"[{level.upper()}] [{agent}] {message}")
        if context:
            print(f"  Context: {json.dumps(context, indent=2)}")
    
    def start_trace(self, trace_id: str, operation: str, agent: str) -> None:
        """Start a new trace for tracking an operation across agents."""
        self.traces[trace_id] = {
            "operation": operation,
            "start_time": datetime.now().isoformat(),
            "agent": agent,
            "spans": []
        }
    
    def add_span(self, trace_id: str, span_name: str, agent: str, duration_ms: float, 
                 metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add a span to a trace."""
        if trace_id not in self.traces:
            self.start_trace(trace_id, span_name, agent)
        
        span = {
            "name": span_name,
            "agent": agent,
            "duration_ms": duration_ms,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.traces[trace_id]["spans"].append(span)
    
    def end_trace(self, trace_id: str, success: bool = True) -> None:
        """End a trace and calculate total duration."""
        if trace_id not in self.traces:
            return
        
        start = datetime.fromisoformat(self.traces[trace_id]["start_time"])
        end = datetime.now()
        duration_ms = (end - start).total_seconds() * 1000
        
        self.traces[trace_id]["end_time"] = end.isoformat()
        self.traces[trace_id]["duration_ms"] = duration_ms
        self.traces[trace_id]["success"] = success
    
    def increment_metric(self, metric_name: str, value: int = 1) -> None:
        """Increment a metric counter."""
        if metric_name in self.metrics:
            self.metrics[metric_name] += value
        else:
            self.metrics[metric_name] = value
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics snapshot."""
        return self.metrics.copy()
    
    def get_trace(self, trace_id: str) -> Optional[Dict[str, Any]]:
        """Get a trace by ID."""
        return self.traces.get(trace_id)
    
    def get_logs(self, agent: Optional[str] = None, level: Optional[str] = None) -> list:
        """Get logs, optionally filtered by agent or level."""
        filtered = self.logs
        if agent:
            filtered = [log for log in filtered if log["agent"] == agent]
        if level:
            filtered = [log for log in filtered if log["level"] == level]
        return filtered

