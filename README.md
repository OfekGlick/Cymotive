# Incident Copilot - AI-Powered Cybersecurity Incident Analysis

> **An copilot system for analyzing and responding to autonomous vehicle cybersecurity incidents using LangGraph, RAG, and Google Gemini**

[![LangGraph](https://img.shields.io/badge/LangGraph-Multi--Agent-blue)](https://github.com/langchain-ai/langgraph)
[![Pinecone](https://img.shields.io/badge/Pinecone-Vector%20DB-green)](https://www.pinecone.io/)
[![Google Gemini](https://img.shields.io/badge/Google-Gemini%202.0-orange)](https://deepmind.google/technologies/gemini/)

---

## 🎯 Project Overview

This system automatically analyzes cybersecurity incident reports, summarizes them, and suggests mitigation strategies using Retrieval-Augmented Generation (RAG).
## 📓  Demo

**Check out the [demo_incident_copilot.ipynb](demo_incident_copilot.ipynb) Jupyter notebook** for a demonstration of the system processing all three test incident reports from `configs/inputs.py`.


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
┌──────────────┐      ┌──────────────┐              │
│ Conservative │      │   Complete   │              │
│   Summary    │      │   Summary    │              │
└──────┬───────┘      └──────┬───────┘              │
       │                     │                      │
       ▼                     ▼                      │
┌──────────────┐      ┌──────────────┐              │
│ Conservative │      │  Retriever   │ ← RAG        │
│  Next Steps  │      │ (Pinecone)   │   Search     │
└──────┬───────┘      └──────┬───────┘              │
       │                     │                      │
       │                     ▼                      │
       │              ┌──────────────┐              │
       │              │  Mitigation  │ ← Context   -│
       │              │    Agent     │   Enhanced   │
       │              └──────┬───────┘   Response   │
       │                     │                      │
       ▼                     ▼                      │
     ┌─────────────────────────┐                    │
     │    Final Response       │                    │
     └─────────────────────────┘                    │
```


## 📁 Project Structure

```
.
├── incident_copilot.py          # Main orchestrator & workflow builder
├── demo_incident_copilot.ipynb  # Interactive demo notebook
│
├── configs/                     # Configuration files
│   ├── config.py                # RAG configuration & API initialization
│   ├── system_prompts.py        # Agent prompt templates
│   └── inputs.py                # Test incident reports
│
├── nodes/                       # Workflow node implementations
│   ├── __init__.py
│   ├── base_node.py             # Abstract base class for all nodes
│   ├── validation_node.py       # 5W1H information extraction
│   ├── router_node.py           # Routing decision logic
│   ├── conservative_summary_node.py      # Conservative path summary
│   ├── conservative_next_steps_node.py   # Conservative recommendations
│   ├── complete_summarization_node.py    # Full incident summary
│   ├── retriever_node.py        # RAG retrieval from Pinecone
│   └── complete_mitigation_node.py       # Context-enhanced mitigation
│
├── data_handling/               # Modular data processing package
│   ├── __init__.py              # Public API exports
│   ├── embeddings.py            # Embedding generation (shared)
│   ├── vector_store.py          # Pinecone operations
│   ├── document_parser.py       # Generic document utilities
│   ├── incident_parser.py       # Incident report parsing
│   └── ingestion_pipeline.py    # Orchestration & batch processing
│
├── data_handling.py             # Legacy ingestion script (deprecated)
├── requirements.txt
└── README.md
```

### Module Responsibilities

#### **Configs Package**
- `config.py` - Centralized RAG configuration, API keys, and Pinecone index management
- `system_prompts.py` - Specialized prompts for each agent (validation, summarization, mitigation)
- `inputs.py` - Test incident reports for demo purposes

#### **Nodes Package**
Multi-agent workflow nodes for incident analysis with conditional routing (conservative vs. complete paths).

📖 **[See nodes/README.md for detailed documentation](nodes/README.md)**

#### **Data Handling Package**
Document ingestion, embedding generation, and vector database operations for RAG.

📖 **[See data_handling/README.md for detailed documentation](data_handling/README.md)**


### Execution Flow:
1. **Validation**: Extracts WHO, WHAT, WHERE, WHEN, IMPACT, STATUS detailed of the incident
2. **Router**: `critical_info_missing = False` → Routes to **Full Path**
3. **Summarization**: Generates concise executive summary
4. **Retriever**: Searches Pinecone for similar CAN bus attacks
5. **Mitigation**: Creates 4-section plan using historical context



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

