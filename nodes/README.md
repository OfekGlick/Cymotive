# Nodes Package

Workflow nodes for the Incident Copilot system. Each node represents a specialized agent in the LangGraph workflow that processes incident reports.

---

## Overview

The `nodes` package implements the core workflow for analyzing cybersecurity incident reports. The workflow uses **conditional routing** to provide either:
- **Conservative Path**: When critical information (WHAT, WHERE, WHEN) is missing, provides a cautious summary and basic next steps
- **Complete Path**: When sufficient information is available, provides full summary and RAG-enhanced mitigation plans with few-shot examples

---

## Package Structure

```
nodes/
├── __init__.py                      # Public API exports
├── base_node.py                     # Abstract base class for all nodes
├── validation_node.py               # 5W1H information extraction
├── router_node.py                   # Routing decision logging
├── conservative_summary_node.py     # Conservative summary generation
├── conservative_next_steps_node.py  # Basic precautionary steps
├── complete_summarization_node.py   # Full incident summary
├── retriever_node.py                # RAG semantic search
└── complete_mitigation_node.py      # Context-enhanced mitigation
```

---

## Workflow Architecture

```
┌─────────────────────┐
│  Validation Node    │  Extract WHO, WHAT, WHERE, WHEN, IMPACT, STATUS
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    Router Node      │  Check: critical_info_missing?
└──────────┬──────────┘
           │
    ┌──────┴───────┐
    │              │
    ▼              ▼
┌────────────┐   ┌─────────┐
│Conservative│   │Complete │
│    Path    │   │  Path   │
└────────────┘   └─────────┘
    │                 │
    ▼                 ▼
┌────────────┐   ┌─────────┐
│Conservative│   │Complete │
│   Summary  │   │Summary  │
└────────────┘   └─────────┘
    │                 │
    ▼                 ▼
┌─────────┐      ┌─────────┐
│Basic    │      │Retriever│  Query description namespace
│NextSteps│      └─────────┘
└─────────┘           │
                      ▼
                 ┌──────────┐
                 │ Complete │  Few-shot learning with
                 │Mitigation│  historical examples
                 └──────────┘
```

---

## Modules

### `base_node.py` - Abstract Base Class

Provides the common interface for all workflow nodes.

**Class: BaseNode**

### `validation_node.py` - Information Extraction

Extracts structured information from incident reports using the **5W1H framework**.

**Class: ValidationNode**

**Extracted Fields:**
- **WHO**: Affected entities (systems, users, organizations)
- **WHAT**: Nature of the incident (attack type, vulnerability)
- **WHERE**: Affected systems/locations
- **WHEN**: Timeline and temporal information
- **IMPACT**: Business and technical impact assessment
- **STATUS**: Current incident status
---

### `router_node.py` - Conditional Routing

Checks the `critical_info_missing` flag and logs the routing decision. The actual routing is handled by LangGraph's conditional edges.

**Class: RouterNode**

**Routing Logic:**
- If `critical_info_missing == True` → Conservative Path
- If `critical_info_missing == False` → Complete Path

---

### `conservative_summary_node.py` - Conservative Summary Generation

Generates faithful summaries when critical information is missing, avoiding speculation.

**Class: ConservativeSummaryNode**

**Behavior:**
- Summarizes only what is explicitly stated in the report
- Identifies missing critical information
- Avoids making assumptions or inferences
- Uses conservative, cautious language

---

### `conservative_next_steps_node.py` - Basic Precautionary Steps

Provides conservative recommendations when critical information is missing.

**Class: ConservativeNextStepsNode**

**Focus Areas:**
- Information gathering priorities
- Basic precautionary measures
- Evidence preservation
- Stakeholder communication
- Escalation procedures

---

### `complete_summarization_node.py` - Full Summary Generation

Generates comprehensive executive-level summaries when sufficient information is available.

**Class: CompleteSummarizationNode**

**Summary Structure:**
- Incident overview
- Key findings
- Impact assessment
- Current status
- Affected entities

---

### `retriever_node.py` - RAG Semantic Search

Searches for similar historical incidents using semantic search in the **description namespace** and extracts recommendations from metadata.

**Class: RetrieverNode**

**Architecture:**
- Queries **only** the `description` namespace in Pinecone
- Uses cross-section metadata to extract recommendations
- Provides few-shot examples (description + recommendations pairs)
---

### `complete_mitigation_node.py` - Context-Enhanced Mitigation

Generates comprehensive mitigation plans using **few-shot learning** with historical incident examples.

**Class: CompleteMitigationNode**

**Few-Shot Learning Approach:**

Provides the LLM with paired examples of incident descriptions and their mitigation strategies from similar historical incidents:

---

## Demo Notebook

See `demo_incident_copilot.ipynb` in the project root for an interactive demonstration of the complete workflow with various test cases.

---