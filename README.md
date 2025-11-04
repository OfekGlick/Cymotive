# Incident Copilot - AI-Powered Cybersecurity Incident Analysis

> **An intelligent multi-agent system for analyzing and responding to autonomous vehicle cybersecurity incidents using LangGraph, RAG, and Google Gemini**

[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-blue)](https://github.com/langchain-ai/langgraph)
[![Pinecone](https://img.shields.io/badge/Pinecone-Vector%20DB-green)](https://www.pinecone.io/)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini%202.0-orange)](https://deepmind.google/technologies/gemini/)

---

## 🎯 Project Overview

This project demonstrates advanced software engineering practices in building production-ready AI systems. It implements a sophisticated **agentic workflow** that automatically analyzes cybersecurity incident reports, provides intelligent summaries, and generates actionable mitigation strategies using Retrieval Augmented Generation (RAG).

### Key Technical Highlights

- **Multi-Agent Architecture**: 7 specialized agents with distinct roles and responsibilities
- **Conditional Workflow Routing**: Dynamic path selection based on information completeness
- **RAG Implementation**: Vector search with Pinecone for contextual incident retrieval
- **Modular Design**: Clean separation of concerns with extensible node-based architecture
- **State Management**: Type-safe workflow state using TypedDict
- **LLM Integration**: Advanced prompt engineering with Google Gemini 2.0 Flash

---

## 🏗️ Architecture

### Workflow Graph

The system implements a conditional branching workflow that adapts based on incident report completeness:

```
┌─────────────┐
│   User      │
│   Input     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Validation  │  ← Extracts WHO, WHAT, WHERE, WHEN, IMPACT, STATUS
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Router    │  ← Checks if critical info (WHEN/IMPACT) is missing
└──────┬──────┘
       │
       ├──────────────────────┬─────────────────────┐
       │ Missing              │ Complete            │
       ▼                      ▼                     │
┌──────────────┐      ┌──────────────┐            │
│ Conservative │      │   Complete   │            │
│   Summary    │      │   Summary    │            │
└──────┬───────┘      └──────┬───────┘            │
       │                     │                     │
       ▼                     ▼                     │
┌──────────────┐      ┌──────────────┐            │
│ Conservative │      │  Retriever   │ ← RAG     │
│  Next Steps  │      │ (Pinecone)   │   Search   │
└──────┬───────┘      └──────┬───────┘            │
       │                     │                     │
       │                     ▼                     │
       │              ┌──────────────┐            │
       │              │  Mitigation  │ ← Context- │
       │              │    Agent     │   Enhanced │
       │              └──────┬───────┘   Response │
       │                     │                     │
       ▼                     ▼                     │
     ┌─────────────────────────┐                 │
     │    Final Response       │                 │
     └─────────────────────────┘                 │
```

### Design Patterns Demonstrated

1. **Strategy Pattern**: Conditional routing between conservative and full analysis paths
2. **Template Method Pattern**: Base node class with common interface (`BaseNode`)
3. **Dependency Injection**: Configuration object passed to all nodes
4. **Single Responsibility Principle**: Each node handles one specific task
5. **Open/Closed Principle**: Extensible node architecture without modifying core workflow

---

## 🔧 Technical Stack

| Technology | Purpose |
|------------|---------|
| **Python 3.x** | Core programming language |
| **LangGraph** | State machine orchestration and workflow management |
| **Google Gemini 2.0 Flash** | Large Language Model for text generation |
| **Pinecone** | Vector database for semantic search and RAG |
| **Google Embeddings (text-embedding-004)** | 768-dimensional text embeddings |

---

## 📁 Project Structure

```
.
├── incident_copilot.py          # Main orchestrator & workflow builder
├── inputs.py                    # Test incident reports
├── configs/                     # Configurations for the scripts
│   ├── system_prompts.py                 # Agent prompt templates
│   ├── config.py                         # Centralized configuration & API initialization
├── nodes/                       # Modular node implementations
│   ├── __init__.py
│   ├── base_node.py             # Abstract base class for all nodes
│   ├── validation_node.py       # 5W1H information extraction
│   ├── router_node.py           # Routing decision logging
│   ├── conservative_summary_node.py      # Conservative path summary
│   ├── conservative_next_steps_node.py   # Conservative recommendations
│   ├── complete_summarization_node.py    # Full incident summary
│   ├── retriever_node.py        # RAG retrieval from Pinecone
│   └── complete_mitigation_node.py       # Context-enhanced mitigation
│
├── data_handling.py             # Document ingestion utilities
├── requirements.txt
└── README.md
```


## 🔄 Workflow Execution Example

### Input (Complete Report):
```
Incident ID: INC-2024-001
Threat Category: CAN Bus DoS Attack
Date: 2024-03-15 14:30 UTC

An attacker injected high-frequency messages on the CAN bus...
```

### Execution Flow:
1. **Validation**: Extracts WHO, WHAT, WHERE, WHEN (✓), IMPACT (✓), STATUS
2. **Router**: `critical_info_missing = False` → Routes to **Full Path**
3. **Summarization**: Generates concise executive summary
4. **Retriever**: Searches Pinecone for similar CAN bus attacks
5. **Mitigation**: Creates 4-section plan using historical context

### Output:
```markdown
## Incident Summary
**INC-2024-001**: CAN Bus DoS Attack
- High-frequency message injection on vehicle CAN bus
- Impact: ECU communication failure, potential safety risk
- Status: Contained, under investigation

## Mitigation Plan

### 1. Immediate Actions
- Isolate affected vehicle from network
- Capture CAN bus traffic logs for forensic analysis
...

### 2. Short-term Response
...
```

---

## 📦 Installation & Setup

```bash
# Clone the repository
git clone <repository-url>
cd Cymotive

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export GEMINI_API_KEY="your-gemini-api-key"
export PINECONE_API_KEY="your-pinecone-api-key"

# Run the copilot
python incident_copilot.py
```

### Configuration

Edit `config.py` to customize:
- Gemini model selection (`gemini-1.5-flash`, etc.)
- Embedding model and dimensions
- Pinecone index name and cloud region
- Generation parameters (temperature, max tokens)

---

## 🧪 Testing

The system includes test incident reports in `inputs.py`:
- **Complete Report - CAN Bus DoS**: Tests full analysis path
- **Complete Report - GPS Spoofing**: Tests RAG retrieval quality
- **Incomplete Report**: Tests conservative path routing

```python
from incident_copilot import IncidentCopilot
from configs.config import RAGConfig
from configs.inputs import COMPLETE_REPORT_CAN_BUS

config = RAGConfig(index_name="incident-reports")
copilot = IncidentCopilot(config)

result = copilot.process(
    incident_report=COMPLETE_REPORT_CAN_BUS,
    verbose=True
)
```