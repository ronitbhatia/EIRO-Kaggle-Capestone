"""
EIRO Platform - Enterprise Incident Response Orchestrator
Kaggle Notebook Version

This is a single-file version suitable for Kaggle notebooks.
All code is consolidated here for easy execution.
"""

# ============================================================================
# SETUP AND IMPORTS
# ============================================================================

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

# Install and import Google Generative AI
try:
    import google.generativeai as genai
except ImportError:
    print("Installing google-generativeai...")
    os.system("pip install -q google-generativeai")
    import google.generativeai as genai

# Configure API key (Kaggle may have this set automatically)
if "GOOGLE_API_KEY" in os.environ:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
else:
    # For Kaggle, try to configure without explicit key
    try:
        genai.configure()
    except:
        print("WARNING: Please set GOOGLE_API_KEY environment variable")
        print("   You can do this in Kaggle by going to Add-ons -> Secrets")


# ============================================================================
# SESSION MANAGER
# ============================================================================

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
    
    def set_state(self, incident_id: str, new_state: str) -> None:
        """Update the incident state."""
        self.update_session(incident_id, {"state": new_state})


# ============================================================================
# OBSERVABILITY
# ============================================================================

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
        print(f"[{level.upper()}] [{agent}] {message}")
    
    def start_trace(self, trace_id: str, operation: str, agent: str) -> None:
        """Start a new trace."""
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
        """End a trace."""
        if trace_id not in self.traces:
            return
        
        start = datetime.fromisoformat(self.traces[trace_id]["start_time"])
        end = datetime.now()
        duration_ms = (end - start).total_seconds() * 1000
        
        self.traces[trace_id]["end_time"] = end.isoformat()
        self.traces[trace_id]["duration_ms"] = duration_ms
        self.traces[trace_id]["success"] = success


# ============================================================================
# TOOLS
# ============================================================================

# Incident Database
class IncidentDatabase:
    def __init__(self):
        self.incidents: Dict[str, Dict[str, Any]] = {}
        self.next_id = 1
    
    def create_incident(self, title: str, description: str, reporter: str, 
                       severity: str = "medium") -> Dict[str, Any]:
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
        return self.incidents.get(incident_id)
    
    def update_incident(self, incident_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if incident_id not in self.incidents:
            return None
        self.incidents[incident_id].update(updates)
        self.incidents[incident_id]["updated_at"] = datetime.now().isoformat()
        return self.incidents[incident_id]

incident_db = IncidentDatabase()

def create_incident_tool(title: str, description: str, reporter: str, severity: str = "medium"):
    return incident_db.create_incident(title, description, reporter, severity)

def get_incident_tool(incident_id: str):
    return incident_db.get_incident(incident_id)

def update_incident_tool(incident_id: str, **updates):
    return incident_db.update_incident(incident_id, updates)

# System Diagnostics
SYSTEM_COMPONENTS = {
    "database": {"status": "healthy", "response_time_ms": 45},
    "api_server": {"status": "healthy", "response_time_ms": 120},
    "cache": {"status": "healthy", "response_time_ms": 5},
    "message_queue": {"status": "healthy", "response_time_ms": 15},
    "file_storage": {"status": "healthy", "response_time_ms": 200}
}

def check_system_health(component: str = None):
    if component:
        if component not in SYSTEM_COMPONENTS:
            return {"error": f"Component '{component}' not found"}
        return {"component": component, **SYSTEM_COMPONENTS[component]}
    return {
        "components": SYSTEM_COMPONENTS,
        "overall_status": "healthy" if all(c["status"] == "healthy" for c in SYSTEM_COMPONENTS.values()) else "degraded"
    }

def diagnose_issue(symptom: str):
    symptom_lower = symptom.lower()
    if "slow" in symptom_lower or "timeout" in symptom_lower:
        return {
            "diagnosis": "Performance degradation",
            "likely_causes": ["High database query latency", "API server overload", "Cache miss rate increase"],
            "recommended_actions": ["Check database query performance", "Review API server metrics", "Investigate cache hit rates"]
        }
    elif "error" in symptom_lower or "failure" in symptom_lower:
        return {
            "diagnosis": "Service failure",
            "likely_causes": ["Component crash", "Resource exhaustion", "Configuration error"],
            "recommended_actions": ["Check component logs", "Review resource usage", "Verify configuration"]
        }
    else:
        return {
            "diagnosis": "Unknown issue",
            "likely_causes": ["Requires further investigation"],
            "recommended_actions": ["Collect more diagnostic information", "Review system logs", "Check recent changes"]
        }

# Knowledge Base
KNOWLEDGE_BASE = [
    {
        "id": "KB-001",
        "title": "Database Connection Timeout Resolution",
        "category": "database",
        "content": "If experiencing database connection timeouts, check: 1) Connection pool size, 2) Network latency, 3) Database server load. Solution: Increase pool size or add read replicas.",
        "tags": ["database", "timeout", "connection", "performance"]
    },
    {
        "id": "KB-002",
        "title": "API Rate Limiting Issues",
        "category": "api",
        "content": "API rate limiting can cause 429 errors. Check API key quotas, implement exponential backoff, or request quota increase from provider.",
        "tags": ["api", "rate-limit", "429", "quota"]
    },
    {
        "id": "KB-003",
        "title": "Cache Invalidation Best Practices",
        "category": "cache",
        "content": "When cache becomes stale, invalidate using TTL or manual invalidation. For distributed caches, use cache tags or pub/sub invalidation.",
        "tags": ["cache", "invalidation", "stale-data"]
    }
]

def search_knowledge_base(query: str, category: str = None):
    query_lower = query.lower()
    results = []
    for article in KNOWLEDGE_BASE:
        if category and article["category"] != category:
            continue
        score = 0
        query_words = query_lower.split()
        if any(word in article["title"].lower() for word in query_words):
            score += 3
        if any(word in article["content"].lower() for word in query_words):
            score += 2
        if score > 0:
            results.append({**article, "relevance_score": score})
    results.sort(key=lambda x: x["relevance_score"], reverse=True)
    return results[:5]

# Notifications
class NotificationService:
    def __init__(self):
        self.notifications = []
    
    def send_notification(self, recipient: str, subject: str, message: str, priority: str = "normal"):
        notification = {
            "id": f"NOTIF-{len(self.notifications) + 1:04d}",
            "recipient": recipient,
            "subject": subject,
            "message": message,
            "priority": priority,
            "sent_at": datetime.now().isoformat()
        }
        self.notifications.append(notification)
        print(f"\nNOTIFICATION [{priority.upper()}]")
        print(f"To: {recipient}")
        print(f"Subject: {subject}")
        print(f"Message: {message}\n")
        return notification

notification_service = NotificationService()

def send_notification_tool(recipient: str, subject: str, message: str, priority: str = "normal"):
    return notification_service.send_notification(recipient, subject, message, priority)


# ============================================================================
# EVALUATION (LLM-as-Judge)
# ============================================================================

class LLMJudge:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model = genai.GenerativeModel(model_name)
    
    def evaluate_agent_response(self, agent_name: str, task: str, response: str, 
                                context: Dict[str, Any] = None) -> Dict[str, Any]:
        evaluation_prompt = f"""You are an expert evaluator assessing an AI agent's performance.

Agent: {agent_name}
Task: {task}
Agent Response: {response}
Context: {context or {}}

Evaluate on: Accuracy, Completeness, Clarity, Actionability, Efficiency (1-10 each).
Provide overall score, strengths, weaknesses, and recommendation (excellent/good/needs_improvement/poor)."""

        try:
            result = self.model.generate_content(evaluation_prompt)
            evaluation_text = result.text
            overall_score = self._extract_score(evaluation_text)
            return {
                "agent": agent_name,
                "task": task,
                "evaluation_text": evaluation_text,
                "overall_score": overall_score,
                "recommendation": self._extract_recommendation(evaluation_text)
            }
        except Exception as e:
            return {"agent": agent_name, "task": task, "error": str(e), "overall_score": None}
    
    def _extract_score(self, text: str) -> float:
        import re
        patterns = [r"overall score[:\s]+(\d+\.?\d*)", r"score[:\s]+(\d+\.?\d*)", r"(\d+\.?\d*)\s*out of 10"]
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                return float(match.group(1))
        return 7.0
    
    def _extract_recommendation(self, text: str) -> str:
        text_lower = text.lower()
        if "excellent" in text_lower:
            return "excellent"
        elif "good" in text_lower:
            return "good"
        elif "needs improvement" in text_lower:
            return "needs_improvement"
        elif "poor" in text_lower:
            return "poor"
        return "good"


# ============================================================================
# AGENTS
# ============================================================================

class TriageAgent:
    def __init__(self, model: genai.GenerativeModel, logger: ObservabilityLogger):
        self.model = model
        self.logger = logger
        self.name = "TriageAgent"
    
    def process(self, incident_data: Dict[str, Any], session_manager: SessionManager) -> Dict[str, Any]:
        incident_id = incident_data.get("id")
        self.logger.log("info", self.name, f"Starting triage for {incident_id}")
        
        if not session_manager.get_session(incident_id):
            session_manager.create_session(incident_id, {"incident": incident_data})
        
        prompt = f"""You are an expert IT incident triage agent. Analyze:
1. Priority level (low, medium, high, critical)
2. Category (performance, error, connectivity, security, other)
3. Initial assessment
4. Recommended next steps

Incident: {incident_data.get('title')}
Description: {incident_data.get('description')}
Severity: {incident_data.get('severity')}
Reporter: {incident_data.get('reporter')}

Provide structured analysis."""

        try:
            response = self.model.generate_content(prompt)
            triage_result = response.text
            
            priority = self._extract_priority(triage_result)
            category = self._extract_category(triage_result)
            
            update_incident_tool(incident_id, priority=priority, category=category)
            
            session_manager.update_session(incident_id, {
                "triage_complete": True,
                "priority": priority,
                "category": category,
                "triage_analysis": triage_result
            })
            session_manager.add_to_history(incident_id, self.name, "triage", triage_result)
            session_manager.set_state(incident_id, "investigation")
            
            self.logger.log("info", self.name, f"Triage complete: Priority={priority}, Category={category}")
            
            return {"status": "success", "priority": priority, "category": category, 
                   "analysis": triage_result, "next_state": "investigation"}
        except Exception as e:
            self.logger.log("error", self.name, f"Triage failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def _extract_priority(self, text: str) -> str:
        text_lower = text.lower()
        if "critical" in text_lower:
            return "critical"
        elif "high" in text_lower:
            return "high"
        elif "low" in text_lower:
            return "low"
        return "medium"
    
    def _extract_category(self, text: str) -> str:
        text_lower = text.lower()
        categories = ["performance", "error", "connectivity", "security"]
        for cat in categories:
            if cat in text_lower:
                return cat
        return "other"


class InvestigationAgent:
    def __init__(self, model: genai.GenerativeModel, logger: ObservabilityLogger):
        self.model = model
        self.logger = logger
        self.name = "InvestigationAgent"
    
    def process(self, incident_id: str, session_manager: SessionManager) -> Dict[str, Any]:
        self.logger.log("info", self.name, f"Starting investigation for {incident_id}")
        
        session = session_manager.get_session(incident_id)
        if not session:
            return {"status": "error", "error": "Session not found"}
        
        incident = get_incident_tool(incident_id)
        if not incident:
            return {"status": "error", "error": "Incident not found"}
        
        system_health = check_system_health()
        diagnosis = diagnose_issue(incident.get("description", ""))
        kb_results = search_knowledge_base(incident.get("description", ""), incident.get("category"))
        
        prompt = f"""You are an expert IT incident investigator. Analyze:

Incident: {incident.get('title')}
Description: {incident.get('description')}
Category: {incident.get('category')}
Priority: {incident.get('priority')}

System Health: {json.dumps(system_health, indent=2)}
Diagnostic Results: {json.dumps(diagnosis, indent=2)}
Knowledge Base: {json.dumps(kb_results[:2], indent=2) if kb_results else 'None'}

Provide: 1) Root cause analysis, 2) Contributing factors, 3) Evidence, 4) Recommended resolution, 5) Estimated time."""

        try:
            response = self.model.generate_content(prompt)
            investigation_result = response.text
            
            session_manager.update_session(incident_id, {
                "investigation_complete": True,
                "root_cause_analysis": investigation_result,
                "diagnostic_data": {"system_health": system_health, "diagnosis": diagnosis, "kb_results": kb_results[:2]}
            })
            session_manager.add_to_history(incident_id, self.name, "investigation", investigation_result)
            session_manager.set_state(incident_id, "resolution")
            
            self.logger.log("info", self.name, "Investigation complete")
            
            return {"status": "success", "root_cause_analysis": investigation_result,
                   "diagnostic_data": {"system_health": system_health, "diagnosis": diagnosis},
                   "next_state": "resolution"}
        except Exception as e:
            self.logger.log("error", self.name, f"Investigation failed: {str(e)}")
            return {"status": "error", "error": str(e)}


class ResolutionAgent:
    def __init__(self, model: genai.GenerativeModel, logger: ObservabilityLogger):
        self.model = model
        self.logger = logger
        self.name = "ResolutionAgent"
    
    def process(self, incident_id: str, session_manager: SessionManager) -> Dict[str, Any]:
        self.logger.log("info", self.name, f"Starting resolution for {incident_id}")
        
        session = session_manager.get_session(incident_id)
        if not session:
            return {"status": "error", "error": "Session not found"}
        
        incident = get_incident_tool(incident_id)
        root_cause = session.get("root_cause_analysis", "")
        diagnostic_data = session.get("diagnostic_data", {})
        
        prompt = f"""You are an expert IT incident resolver. Create resolution plan:

Incident: {incident.get('title')}
Root Cause: {root_cause}
Diagnostic Data: {json.dumps(diagnostic_data, indent=2)}

Provide: 1) Step-by-step plan, 2) Commands/actions, 3) Verification, 4) Prevention, 5) Summary."""

        try:
            response = self.model.generate_content(prompt)
            resolution_plan = response.text
            resolution_summary = resolution_plan[:200] if len(resolution_plan) > 200 else resolution_plan
            
            update_incident_tool(incident_id, resolution=resolution_summary)
            
            session_manager.update_session(incident_id, {
                "resolution_complete": True,
                "resolution_plan": resolution_plan,
                "resolution_summary": resolution_summary
            })
            session_manager.add_to_history(incident_id, self.name, "resolution", resolution_plan)
            session_manager.set_state(incident_id, "closed")
            
            self.logger.log("info", self.name, "Resolution complete")
            
            return {"status": "success", "resolution_plan": resolution_plan,
                   "resolution_summary": resolution_summary, "next_state": "closed"}
        except Exception as e:
            self.logger.log("error", self.name, f"Resolution failed: {str(e)}")
            return {"status": "error", "error": str(e)}


class CommunicationAgent:
    def __init__(self, model: genai.GenerativeModel, logger: ObservabilityLogger):
        self.model = model
        self.logger = logger
        self.name = "CommunicationAgent"
    
    def process(self, incident_id: str, stage: str, session_manager: SessionManager) -> Dict[str, Any]:
        self.logger.log("info", self.name, f"Generating communication for {incident_id} at {stage}")
        
        session = session_manager.get_session(incident_id)
        incident = get_incident_tool(incident_id)
        
        if not session or not incident:
            return {"status": "error", "error": "Session or incident not found"}
        
        prompt = f"""You are a professional IT communication agent. Generate status update:

Incident: {incident.get('title')}
Stage: {stage}
Priority: {incident.get('priority')}
Reporter: {incident.get('reporter')}

Create: 1) Subject, 2) Brief status (2-3 sentences), 3) Progress, 4) Next steps, 5) Actions needed."""

        try:
            response = self.model.generate_content(prompt)
            communication_text = response.text
            
            subject = f"Incident Update - {stage.title()}"
            priority_map = {"critical": "urgent", "high": "high", "medium": "normal", "low": "low"}
            notif_priority = priority_map.get(incident.get("priority", "medium"), "normal")
            
            send_notification_tool(incident.get("reporter"), subject, communication_text, notif_priority)
            session_manager.add_to_history(incident_id, self.name, f"communication_{stage}", communication_text)
            
            self.logger.log("info", self.name, f"Communication sent for {stage}")
            
            return {"status": "success", "subject": subject, "message": communication_text}
        except Exception as e:
            self.logger.log("error", self.name, f"Communication failed: {str(e)}")
            return {"status": "error", "error": str(e)}


# ============================================================================
# ORCHESTRATOR
# ============================================================================

class IncidentOrchestrator:
    def __init__(self, api_key: Optional[str] = None):
        if api_key:
            genai.configure(api_key=api_key)
        elif os.getenv("GOOGLE_API_KEY"):
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        else:
            try:
                genai.configure()
            except:
                print("WARNING: API key not configured")
        
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        self.session_manager = SessionManager()
        self.logger = ObservabilityLogger()
        self.judge = LLMJudge()
        
        self.triage_agent = TriageAgent(self.model, self.logger)
        self.investigation_agent = InvestigationAgent(self.model, self.logger)
        self.resolution_agent = ResolutionAgent(self.model, self.logger)
        self.communication_agent = CommunicationAgent(self.model, self.logger)
    
    def handle_incident(self, title: str, description: str, reporter: str, 
                       severity: str = "medium", evaluate: bool = True) -> Dict[str, Any]:
        trace_id = f"incident-{len(self.session_manager.sessions) + 1}"
        self.logger.start_trace(trace_id, "handle_incident", "Orchestrator")
        
        try:
            self.logger.log("info", "Orchestrator", "Creating incident")
            incident = create_incident_tool(title, description, reporter, severity)
            incident_id = incident["id"]
            
            self.logger.add_span(trace_id, "triage", "TriageAgent", 0)
            triage_result = self.triage_agent.process(incident, self.session_manager)
            self.communication_agent.process(incident_id, "triage", self.session_manager)
            
            if triage_result.get("status") != "success":
                raise Exception(f"Triage failed: {triage_result.get('error')}")
            
            self.logger.add_span(trace_id, "investigation", "InvestigationAgent", 0)
            investigation_result = self.investigation_agent.process(incident_id, self.session_manager)
            self.communication_agent.process(incident_id, "investigation", self.session_manager)
            
            if investigation_result.get("status") != "success":
                raise Exception(f"Investigation failed: {investigation_result.get('error')}")
            
            self.logger.add_span(trace_id, "resolution", "ResolutionAgent", 0)
            resolution_result = self.resolution_agent.process(incident_id, self.session_manager)
            self.communication_agent.process(incident_id, "resolution", self.session_manager)
            
            if resolution_result.get("status") != "success":
                raise Exception(f"Resolution failed: {resolution_result.get('error')}")
            
            final_incident = get_incident_tool(incident_id)
            self.logger.log("info", "Orchestrator", f"Incident {incident_id} resolved")
            
            evaluation_results = None
            if evaluate:
                self.logger.log("info", "Orchestrator", "Running agent evaluation")
                evaluation_results = self._evaluate_agents(incident_id, {
                    "triage": triage_result,
                    "investigation": investigation_result,
                    "resolution": resolution_result
                })
            
            self.logger.end_trace(trace_id, success=True)
            
            return {
                "incident_id": incident_id,
                "status": "resolved",
                "triage": triage_result,
                "investigation": investigation_result,
                "resolution": resolution_result,
                "final_incident": final_incident,
                "evaluation": evaluation_results,
                "session": self.session_manager.get_session(incident_id)
            }
            
        except Exception as e:
            self.logger.log("error", "Orchestrator", f"Failed: {str(e)}")
            self.logger.end_trace(trace_id, success=False)
            return {"status": "error", "error": str(e)}
    
    def _evaluate_agents(self, incident_id: str, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        evaluations = {}
        
        if "triage" in agent_results:
            triage_eval = self.judge.evaluate_agent_response(
                "TriageAgent", "Classify and prioritize incident",
                agent_results["triage"].get("analysis", ""), {"incident_id": incident_id}
            )
            evaluations["triage"] = triage_eval
        
        if "investigation" in agent_results:
            inv_eval = self.judge.evaluate_agent_response(
                "InvestigationAgent", "Investigate root cause",
                agent_results["investigation"].get("root_cause_analysis", ""), {"incident_id": incident_id}
            )
            evaluations["investigation"] = inv_eval
        
        if "resolution" in agent_results:
            res_eval = self.judge.evaluate_agent_response(
                "ResolutionAgent", "Generate resolution plan",
                agent_results["resolution"].get("resolution_plan", ""), {"incident_id": incident_id}
            )
            evaluations["resolution"] = res_eval
        
        return evaluations


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    print("="*60)
    print("EIRO Platform - Enterprise Incident Response Orchestrator")
    print("="*60)
    print()
    
    # Initialize
    orchestrator = IncidentOrchestrator()
    
    # Example incident
    result = orchestrator.handle_incident(
        title="Database Connection Timeout",
        description="Users are experiencing database connection timeouts when accessing the application. Error rate has increased by 40% in the last hour.",
        reporter="ops-team@company.com",
        severity="high",
        evaluate=True
    )
    
    print("\n" + "="*60)
    print("INCIDENT RESOLUTION SUMMARY")
    print("="*60)
    print(f"Incident ID: {result.get('incident_id')}")
    print(f"Status: {result.get('status')}")
    
    if result.get("evaluation"):
        print("\nAgent Evaluations:")
        for agent, eval_data in result["evaluation"].items():
            score = eval_data.get('overall_score', 'N/A')
            rec = eval_data.get('recommendation', 'N/A')
            print(f"  {agent}: Score {score}/10 - {rec}")

