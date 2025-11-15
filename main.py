"""
EIRO Platform - Enterprise Incident Response Orchestrator

Main orchestration file that coordinates multiple agents to handle enterprise incidents.
This demonstrates:
- Multi-agent system (sequential orchestration)
- Custom tools integration
- Session and memory management
- Observability (logging and tracing)
- Agent evaluation (LLM-as-judge)
"""

import os
import google.generativeai as genai
from typing import Dict, Any, Optional
import json

# Import utilities
from utils.session_manager import SessionManager
from utils.observability import ObservabilityLogger

# Import tools
from tools.incident_db import (
    create_incident_tool, get_incident_tool, update_incident_tool
)
from tools.system_diagnostics import check_system_health, diagnose_issue, get_system_metrics
from tools.knowledge_base import search_knowledge_base, get_article
from tools.notifications import send_notification_tool

# Import evaluation
from evaluation.llm_judge import LLMJudge


class TriageAgent:
    """
    Incident Triage Agent - Classifies and prioritizes incoming incidents.
    
    This agent demonstrates the first stage of multi-agent orchestration.
    """
    
    def __init__(self, model: genai.GenerativeModel, logger: ObservabilityLogger):
        self.model = model
        self.logger = logger
        self.name = "TriageAgent"
    
    def process(self, incident_data: Dict[str, Any], session_manager: SessionManager) -> Dict[str, Any]:
        """Triage an incident: classify, prioritize, and categorize."""
        incident_id = incident_data.get("id")
        self.logger.log("info", self.name, f"Starting triage for {incident_id}")
        
        # Create session if it doesn't exist
        if not session_manager.get_session(incident_id):
            session_manager.create_session(incident_id, {"incident": incident_data})
        
        # Prepare prompt with incident details
        prompt = f"""You are an expert IT incident triage agent. Analyze the following incident and provide:
1. Priority level (low, medium, high, critical)
2. Category (performance, error, connectivity, security, other)
3. Initial assessment
4. Recommended next steps

Incident Details:
Title: {incident_data.get('title')}
Description: {incident_data.get('description')}
Severity: {incident_data.get('severity')}
Reporter: {incident_data.get('reporter')}

Provide your analysis in a structured format."""

        try:
            response = self.model.generate_content(prompt)
            triage_result = response.text
            
            # Extract structured information (simplified parsing)
            priority = self._extract_priority(triage_result)
            category = self._extract_category(triage_result)
            
            # Update incident in database
            update_incident_tool(incident_id, priority=priority, category=category)
            
            # Update session
            session_manager.update_session(incident_id, {
                "triage_complete": True,
                "priority": priority,
                "category": category,
                "triage_analysis": triage_result
            })
            session_manager.add_to_history(incident_id, self.name, "triage", triage_result)
            session_manager.set_state(incident_id, "investigation")
            
            self.logger.log("info", self.name, f"Triage complete: Priority={priority}, Category={category}")
            
            return {
                "status": "success",
                "priority": priority,
                "category": category,
                "analysis": triage_result,
                "next_state": "investigation"
            }
        except Exception as e:
            self.logger.log("error", self.name, f"Triage failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def _extract_priority(self, text: str) -> str:
        """Extract priority from response text."""
        text_lower = text.lower()
        if "critical" in text_lower:
            return "critical"
        elif "high" in text_lower:
            return "high"
        elif "low" in text_lower:
            return "low"
        return "medium"
    
    def _extract_category(self, text: str) -> str:
        """Extract category from response text."""
        text_lower = text.lower()
        categories = ["performance", "error", "connectivity", "security"]
        for cat in categories:
            if cat in text_lower:
                return cat
        return "other"


class InvestigationAgent:
    """
    Investigation Agent - Analyzes root causes using diagnostic tools.
    
    This agent demonstrates tool usage and deeper analysis.
    """
    
    def __init__(self, model: genai.GenerativeModel, logger: ObservabilityLogger):
        self.model = model
        self.logger = logger
        self.name = "InvestigationAgent"
    
    def process(self, incident_id: str, session_manager: SessionManager) -> Dict[str, Any]:
        """Investigate incident root cause using tools."""
        self.logger.log("info", self.name, f"Starting investigation for {incident_id}")
        
        session = session_manager.get_session(incident_id)
        if not session:
            return {"status": "error", "error": "Session not found"}
        
        incident = get_incident_tool(incident_id)
        if not incident:
            return {"status": "error", "error": "Incident not found"}
        
        # Use diagnostic tools
        system_health = check_system_health()
        diagnosis = diagnose_issue(incident.get("description", ""))
        
        # Search knowledge base
        kb_results = search_knowledge_base(incident.get("description", ""), incident.get("category"))
        
        # Prepare investigation prompt
        prompt = f"""You are an expert IT incident investigator. Analyze the following incident and determine the root cause.

Incident: {incident.get('title')}
Description: {incident.get('description')}
Category: {incident.get('category')}
Priority: {incident.get('priority')}

System Health: {json.dumps(system_health, indent=2)}
Diagnostic Results: {json.dumps(diagnosis, indent=2)}
Knowledge Base Results: {json.dumps(kb_results[:2], indent=2) if kb_results else 'None'}

Provide:
1. Root cause analysis
2. Contributing factors
3. Evidence from diagnostics
4. Recommended resolution approach
5. Estimated resolution time"""

        try:
            response = self.model.generate_content(prompt)
            investigation_result = response.text
            
            # Update session
            session_manager.update_session(incident_id, {
                "investigation_complete": True,
                "root_cause_analysis": investigation_result,
                "diagnostic_data": {
                    "system_health": system_health,
                    "diagnosis": diagnosis,
                    "kb_results": kb_results[:2]
                }
            })
            session_manager.add_to_history(incident_id, self.name, "investigation", investigation_result)
            session_manager.set_state(incident_id, "resolution")
            
            self.logger.log("info", self.name, "Investigation complete")
            
            return {
                "status": "success",
                "root_cause_analysis": investigation_result,
                "diagnostic_data": {
                    "system_health": system_health,
                    "diagnosis": diagnosis
                },
                "next_state": "resolution"
            }
        except Exception as e:
            self.logger.log("error", self.name, f"Investigation failed: {str(e)}")
            return {"status": "error", "error": str(e)}


class ResolutionAgent:
    """
    Resolution Agent - Proposes and documents fixes.
    
    This agent demonstrates action planning and resolution documentation.
    """
    
    def __init__(self, model: genai.GenerativeModel, logger: ObservabilityLogger):
        self.model = model
        self.logger = logger
        self.name = "ResolutionAgent"
    
    def process(self, incident_id: str, session_manager: SessionManager) -> Dict[str, Any]:
        """Generate resolution plan and execute fixes."""
        self.logger.log("info", self.name, f"Starting resolution for {incident_id}")
        
        session = session_manager.get_session(incident_id)
        if not session:
            return {"status": "error", "error": "Session not found"}
        
        incident = get_incident_tool(incident_id)
        root_cause = session.get("root_cause_analysis", "")
        diagnostic_data = session.get("diagnostic_data", {})
        
        # Prepare resolution prompt
        prompt = f"""You are an expert IT incident resolver. Create a resolution plan for this incident.

Incident: {incident.get('title')}
Root Cause Analysis: {root_cause}
Diagnostic Data: {json.dumps(diagnostic_data, indent=2)}

Provide:
1. Step-by-step resolution plan
2. Commands or actions to execute (if applicable)
3. Verification steps
4. Prevention measures
5. Resolution summary for documentation"""

        try:
            response = self.model.generate_content(prompt)
            resolution_plan = response.text
            
            # Extract resolution summary
            resolution_summary = self._extract_resolution_summary(resolution_plan)
            
            # Update incident
            update_incident_tool(incident_id, resolution=resolution_summary)
            
            # Update session
            session_manager.update_session(incident_id, {
                "resolution_complete": True,
                "resolution_plan": resolution_plan,
                "resolution_summary": resolution_summary
            })
            session_manager.add_to_history(incident_id, self.name, "resolution", resolution_plan)
            session_manager.set_state(incident_id, "closed")
            
            self.logger.log("info", self.name, "Resolution complete")
            
            return {
                "status": "success",
                "resolution_plan": resolution_plan,
                "resolution_summary": resolution_summary,
                "next_state": "closed"
            }
        except Exception as e:
            self.logger.log("error", self.name, f"Resolution failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def _extract_resolution_summary(self, text: str) -> str:
        """Extract a concise resolution summary."""
        # Look for "Resolution summary" or "Summary" section
        lines = text.split("\n")
        summary_lines = []
        in_summary = False
        
        for line in lines:
            if "resolution summary" in line.lower() or "summary" in line.lower():
                in_summary = True
                continue
            if in_summary and line.strip():
                summary_lines.append(line.strip())
            if in_summary and not line.strip() and summary_lines:
                break
        
        return "\n".join(summary_lines) if summary_lines else text[:200]


class CommunicationAgent:
    """
    Communication Agent - Generates status updates and notifications.
    
    This agent demonstrates stakeholder communication throughout the incident lifecycle.
    """
    
    def __init__(self, model: genai.GenerativeModel, logger: ObservabilityLogger):
        self.model = model
        self.logger = logger
        self.name = "CommunicationAgent"
    
    def process(self, incident_id: str, stage: str, session_manager: SessionManager) -> Dict[str, Any]:
        """Generate and send communication for a given stage."""
        self.logger.log("info", self.name, f"Generating communication for {incident_id} at stage {stage}")
        
        session = session_manager.get_session(incident_id)
        incident = get_incident_tool(incident_id)
        
        if not session or not incident:
            return {"status": "error", "error": "Session or incident not found"}
        
        # Prepare communication prompt
        prompt = f"""You are a professional IT communication agent. Generate a clear, concise status update for stakeholders.

Incident: {incident.get('title')}
Current Stage: {stage}
Priority: {incident.get('priority')}
Reporter: {incident.get('reporter')}

Session Data: {json.dumps(session, indent=2, default=str)}

Create:
1. Subject line for the update
2. Brief status message (2-3 sentences)
3. Current status and progress
4. Next steps or expected timeline
5. Any action required from stakeholders"""

        try:
            response = self.model.generate_content(prompt)
            communication_text = response.text
            
            # Extract subject and message
            subject = self._extract_subject(communication_text, stage)
            message = communication_text
            
            # Send notification
            priority_map = {
                "critical": "urgent",
                "high": "high",
                "medium": "normal",
                "low": "low"
            }
            notif_priority = priority_map.get(incident.get("priority", "medium"), "normal")
            
            send_notification_tool(
                incident.get("reporter"),
                subject,
                message,
                notif_priority
            )
            
            session_manager.add_to_history(incident_id, self.name, f"communication_{stage}", communication_text)
            
            self.logger.log("info", self.name, f"Communication sent for {stage}")
            
            return {
                "status": "success",
                "subject": subject,
                "message": message
            }
        except Exception as e:
            self.logger.log("error", self.name, f"Communication failed: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def _extract_subject(self, text: str, stage: str) -> str:
        """Extract or generate subject line."""
        lines = text.split("\n")
        for line in lines:
            if "subject" in line.lower() and ":" in line:
                return line.split(":", 1)[1].strip()
        return f"Incident Update - {stage.title()}"


class IncidentOrchestrator:
    """
    Main orchestrator that coordinates all agents in a sequential workflow.
    
    This demonstrates the multi-agent system concept with sequential orchestration.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize orchestrator with Gemini model and all agents."""
        # Set up Gemini API
        if api_key:
            genai.configure(api_key=api_key)
        elif os.getenv("GOOGLE_API_KEY"):
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        else:
            # For Kaggle, API key might be set automatically
            try:
                genai.configure()
            except:
                print("Warning: API key not configured. Please set GOOGLE_API_KEY environment variable.")
        
        self.model = genai.GenerativeModel("gemini-2.5-flash")
        
        # Initialize utilities
        self.session_manager = SessionManager()
        self.logger = ObservabilityLogger()
        self.judge = LLMJudge()
        
        # Initialize agents
        self.triage_agent = TriageAgent(self.model, self.logger)
        self.investigation_agent = InvestigationAgent(self.model, self.logger)
        self.resolution_agent = ResolutionAgent(self.model, self.logger)
        self.communication_agent = CommunicationAgent(self.model, self.logger)
    
    def handle_incident(self, title: str, description: str, reporter: str, 
                       severity: str = "medium", evaluate: bool = True) -> Dict[str, Any]:
        """
        Main entry point: handle an incident through the full lifecycle.
        
        This demonstrates sequential multi-agent orchestration.
        """
        trace_id = f"incident-{len(self.session_manager.sessions) + 1}"
        self.logger.start_trace(trace_id, "handle_incident", "Orchestrator")
        
        try:
            # Step 1: Create incident
            self.logger.log("info", "Orchestrator", "Creating incident")
            incident = create_incident_tool(title, description, reporter, severity)
            incident_id = incident["id"]
            
            # Step 2: Triage
            self.logger.add_span(trace_id, "triage", "TriageAgent", 0)
            triage_result = self.triage_agent.process(incident, self.session_manager)
            self.communication_agent.process(incident_id, "triage", self.session_manager)
            
            if triage_result.get("status") != "success":
                raise Exception(f"Triage failed: {triage_result.get('error')}")
            
            # Step 3: Investigation
            self.logger.add_span(trace_id, "investigation", "InvestigationAgent", 0)
            investigation_result = self.investigation_agent.process(incident_id, self.session_manager)
            self.communication_agent.process(incident_id, "investigation", self.session_manager)
            
            if investigation_result.get("status") != "success":
                raise Exception(f"Investigation failed: {investigation_result.get('error')}")
            
            # Step 4: Resolution
            self.logger.add_span(trace_id, "resolution", "ResolutionAgent", 0)
            resolution_result = self.resolution_agent.process(incident_id, self.session_manager)
            self.communication_agent.process(incident_id, "resolution", self.session_manager)
            
            if resolution_result.get("status") != "success":
                raise Exception(f"Resolution failed: {resolution_result.get('error')}")
            
            # Step 5: Close incident
            final_incident = get_incident_tool(incident_id)
            self.logger.log("info", "Orchestrator", f"Incident {incident_id} resolved successfully")
            
            # Step 6: Evaluation (if requested)
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
            self.logger.log("error", "Orchestrator", f"Incident handling failed: {str(e)}")
            self.logger.end_trace(trace_id, success=False)
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _evaluate_agents(self, incident_id: str, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate all agents using LLM-as-judge."""
        evaluations = {}
        
        # Evaluate Triage Agent
        if "triage" in agent_results:
            triage_eval = self.judge.evaluate_agent_response(
                "TriageAgent",
                "Classify and prioritize incident",
                agent_results["triage"].get("analysis", ""),
                {"incident_id": incident_id}
            )
            evaluations["triage"] = triage_eval
        
        # Evaluate Investigation Agent
        if "investigation" in agent_results:
            inv_eval = self.judge.evaluate_agent_response(
                "InvestigationAgent",
                "Investigate root cause using diagnostic tools",
                agent_results["investigation"].get("root_cause_analysis", ""),
                {"incident_id": incident_id}
            )
            evaluations["investigation"] = inv_eval
        
        # Evaluate Resolution Agent
        if "resolution" in agent_results:
            res_eval = self.judge.evaluate_agent_response(
                "ResolutionAgent",
                "Generate resolution plan",
                agent_results["resolution"].get("resolution_plan", ""),
                {"incident_id": incident_id}
            )
            evaluations["resolution"] = res_eval
        
        return evaluations


# Example usage
if __name__ == "__main__":
    # Initialize orchestrator
    orchestrator = IncidentOrchestrator()
    
    # Example incident
    result = orchestrator.handle_incident(
        title="Database Connection Timeout",
        description="Users are experiencing database connection timeouts when accessing the application. Error rate has increased by 40% in the last hour.",
        reporter="ops-team@company.com",
        severity="high",
        evaluate=True
    )
    
    print("\n" + "="*50)
    print("INCIDENT RESOLUTION SUMMARY")
    print("="*50)
    print(f"Incident ID: {result.get('incident_id')}")
    print(f"Status: {result.get('status')}")
    
    if result.get("evaluation"):
        print("\nAgent Evaluations:")
        for agent, eval_data in result["evaluation"].items():
            print(f"  {agent}: Score {eval_data.get('overall_score', 'N/A')} - {eval_data.get('recommendation', 'N/A')}")

