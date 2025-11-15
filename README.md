# EIRO Platform

**Enterprise Incident Response Orchestrator**

A multi-agent AI system for automated enterprise incident management using Google Gemini and ADK.

## Overview

EIRO orchestrates four specialized agents to handle IT incidents from triage to resolution:
- **Triage Agent**: Classifies and prioritizes incidents
- **Investigation Agent**: Analyzes root causes using diagnostic tools
- **Resolution Agent**: Generates resolution plans
- **Communication Agent**: Keeps stakeholders informed

Includes LLM-as-judge evaluation for continuous improvement.

## Installation

```bash
pip install -r requirements.txt
```

Set your Google API key:
```bash
export GOOGLE_API_KEY="your-api-key"
```

Or in Python:
```python
import os
os.environ["GOOGLE_API_KEY"] = "your-api-key"
```

## Usage

```python
from main import IncidentOrchestrator

# Initialize
orchestrator = IncidentOrchestrator()

# Handle an incident
result = orchestrator.handle_incident(
    title="Database Connection Timeout",
    description="Users experiencing database connection timeouts...",
    reporter="ops-team@company.com",
    severity="high",
    evaluate=True
)

print(f"Incident {result['incident_id']} resolved!")
print(f"Evaluation scores: {result['evaluation']}")
```

## Project Structure

```
CapeStone/
├── main.py                 # Main orchestration
├── agents/                 # Agent implementations
├── tools/                  # Custom tools
│   ├── incident_db.py
│   ├── system_diagnostics.py
│   ├── knowledge_base.py
│   └── notifications.py
├── utils/                  # Utilities
│   ├── session_manager.py
│   └── observability.py
├── evaluation/             # LLM-as-judge
│   └── llm_judge.py
├── requirements.txt
└── WRITEUP.md             # Full project writeup
```

## Course Concepts

- Multi-agent system (sequential orchestration)
- Tools (custom tools for incident management)
- Agent evaluation (LLM-as-judge)
- Sessions and memory (session state management)
- Observability (logging, tracing, metrics)

## License

This project is for educational purposes as part of the "5-Day AI Agents Intensive Course with Google."

