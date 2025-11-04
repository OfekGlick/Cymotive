"""
Incident Copilot - Agentic Workflow for Incident Analysis
Uses LangGraph with specialized agents and conditional routing based on information completeness.

Workflow:
1. User provides full incident report
2. Validation Agent - Extracts WHO, WHAT, WHERE, WHEN, IMPACT, STATUS; flags critical missing info
3. Router - Checks if critical information (WHEN or IMPACT) is missing

**If CRITICAL INFO MISSING (Conservative Path):**
   4a. Conservative Summary Agent - Faithful summary of ONLY what's stated in the report
   5a. Conservative Next Steps Agent - Very conservative recommendations (NOT full mitigation)

**If CRITICAL INFO PRESENT (Full Path):**
   4b. Summarization Agent - Executive summary of the complete incident
   5b. Retriever - Searches Pinecone for similar incidents and recommendations
   6b. Mitigation Agent - Comprehensive mitigation plan using summary + historical context

Each agent has its own system message defining its role and behavior.
All agents use system/human message separation for proper role definition.
"""

import os
from typing import TypedDict, List, Dict, Any

from langgraph.graph import StateGraph, END

from config import RAGConfig
from nodes import (
    ValidationNode,
    RouterNode,
    ConservativeSummaryNode,
    ConservativeNextStepsNode,
    CompleteSummarizationNode,
    RetrieverNode,
    CompleteMitigationNode
)


# Define the state schema for the copilot workflow
class CopilotState(TypedDict):
    """State schema for the incident copilot workflow."""
    # Input - User provides full incident report
    incident_report: str  # Full incident report text from user

    # Validation - Standard information extraction
    who: str  # Who was involved (system, attacker, vehicle, etc.)
    what: str  # What happened (the incident/attack)
    where: str  # Where it occurred (system component, location)
    when: str  # When it happened (timestamp, date)
    impact: str  # What was affected and severity
    status: str  # Current status of the incident
    critical_info_missing: bool  # True if 'when' or 'impact' is missing

    # Summarization
    summary: str
    description: str  # Extracted description section for retrieval

    # Retrieval for Mitigation
    retrieved_incidents: List[Dict[str, Any]]  # Similar historical incidents
    retrieved_recommendations: List[str]  # Recommendations from similar incidents

    # Mitigation
    mitigation_plan: str

    # Output
    final_response: str
    metadata: Dict[str, Any]

    # Error handling
    error: str


class IncidentCopilot:
    """
    Agentic copilot for incident analysis using LangGraph.
    Always provides both incident summary and mitigation strategies.
    """

    def __init__(self, config: RAGConfig):
        """
        Initialize the incident copilot with modular node classes.

        Args:
            config: RAG configuration object
        """
        self.config = config

        # Initialize node instances
        self._init_nodes()

        # Build workflow graph
        self.graph = self._build_graph()
        print("Incident Copilot initialized with modular nodes!")

    def _init_nodes(self):
        """Initialize all node instances."""
        self.validation_node = ValidationNode(self.config)
        self.router_node = RouterNode(self.config)
        self.conservative_summary_node = ConservativeSummaryNode(self.config)
        self.conservative_nextsteps_node = ConservativeNextStepsNode(self.config)
        self.summarization_node = CompleteSummarizationNode(self.config)
        self.retriever_node = RetrieverNode(self.config)
        self.mitigation_node = CompleteMitigationNode(self.config)

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow with conditional routing based on critical info."""
        workflow = StateGraph(CopilotState)

        # Add nodes using the modular node instances
        workflow.add_node("validate", self.validation_node)
        workflow.add_node("router", self.router_node)

        # Conservative path (critical info missing)
        workflow.add_node("conservative_summary", self.conservative_summary_node)
        workflow.add_node("conservative_nextsteps", self.conservative_nextsteps_node)

        # Full path (critical info present)
        workflow.add_node("summarize", self.summarization_node)
        workflow.add_node("retrieve", self.retriever_node)
        workflow.add_node("mitigate", self.mitigation_node)

        # Set entry point
        workflow.set_entry_point("validate")

        # Validation → Router
        workflow.add_edge("validate", "router")

        # Conditional routing based on critical_info_missing
        workflow.add_conditional_edges(
            "router",
            self._route_by_critical_info,
            {
                "conservative": "conservative_summary",
                "full": "summarize"
            }
        )

        # Conservative path: conservative_summary → conservative_nextsteps → END
        workflow.add_edge("conservative_summary", "conservative_nextsteps")
        workflow.add_edge("conservative_nextsteps", END)

        # Full path: summarize → retrieve → mitigate → END
        workflow.add_edge("summarize", "retrieve")
        workflow.add_edge("retrieve", "mitigate")
        workflow.add_edge("mitigate", END)

        return workflow.compile()

    def _route_by_critical_info(self, state: CopilotState) -> str:
        """
        Routing function that decides path based on critical_info_missing flag.

        Args:
            state: Current workflow state

        Returns:
            "conservative" if critical info missing, "full" otherwise
        """
        if state['critical_info_missing']:
            return "conservative"
        else:
            return "full"

    def visualize_graph(self, output_path: str = None) -> str:
        """
        Generate a Mermaid diagram of the workflow graph.

        Args:
            output_path: Optional path to save the diagram as PNG

        Returns:
            Mermaid diagram syntax as string
        """
        try:
            # Get Mermaid syntax
            mermaid_syntax = self.graph.get_graph().draw_mermaid()
            print("Graph Mermaid Diagram:")
            print(mermaid_syntax)

            # If output path provided, try to generate PNG
            if output_path:
                try:
                    mermaid_png = self.graph.get_graph().draw_mermaid_png()
                    with open(output_path, 'wb') as f:
                        f.write(mermaid_png)
                    print(f"\nGraph visualization saved to: {output_path}")
                except Exception as e:
                    print(f"\nCould not generate PNG (requires 'mermaid' CLI): {e}")
                    print("You can paste the Mermaid syntax into https://mermaid.live for visualization")

            return mermaid_syntax

        except Exception as e:
            print(f"Error generating graph visualization: {e}")
            return ""

    def process(
        self,
        incident_report: str,
        verbose: bool = False
    ) -> Dict[str, Any]:
        """
        Process incident report through the agentic workflow.

        Args:
            incident_report: Full incident report text from user
            verbose: Whether to print detailed output

        Returns:
            Complete response with metadata including validation results
        """
        print(f"\n{'='*60}")
        print(f"INCIDENT COPILOT")
        print(f"{'='*60}")
        print(f"Processing incident report...")
        print(f"{'='*60}\n")

        # Initialize state
        initial_state: CopilotState = {
            'incident_report': incident_report,
            # Validation fields (will be populated by validation node)
            'who': '',
            'what': '',
            'where': '',
            'when': '',
            'impact': '',
            'status': '',
            'critical_info_missing': False,
            # Other fields
            'description': '',
            'summary': '',
            'retrieved_incidents': [],
            'retrieved_recommendations': [],
            'mitigation_plan': '',
            'final_response': '',
            'metadata': {},
            'error': ''
        }

        # Run through the graph
        final_state = self.graph.invoke(initial_state)

        result = {
            'response': final_state['final_response'],
            'summary': final_state['summary'],
            'mitigation_plan': final_state['mitigation_plan'],
            'validation': {
                'who': final_state['who'],
                'what': final_state['what'],
                'where': final_state['where'],
                'when': final_state['when'],
                'impact': final_state['impact'],
                'status': final_state['status'],
                'critical_info_missing': final_state['critical_info_missing']
            },
            'retrieved_incidents': final_state.get('retrieved_incidents', []),
            'metadata': {
                'num_retrieved_incidents': len(final_state.get('retrieved_incidents', [])),
                'num_recommendations': len(final_state.get('retrieved_recommendations', [])),
                'error': final_state.get('error', '')
            }
        }

        if verbose:
            print(f"\n{'='*60}")
            print(f"RESULT")
            print(f"{'='*60}")
            print(f"Validation - Critical Info Missing: {result['validation']['critical_info_missing']}")
            print(f"Retrieved Incidents: {result['metadata']['num_retrieved_incidents']}")
            print(f"Retrieved Recommendations: {result['metadata']['num_recommendations']}")
            print(f"\nResponse:\n{result['response']}")
            print(f"{'='*60}\n")

        return result


def main():
    """
    Example usage of the Incident Copilot.
    """
    from inputs import (
        COMPLETE_REPORT_CAN_BUS,
        COMPLETE_REPORT_GPS_SPOOFING,
        INCOMPLETE_REPORT_SUSPICIOUS_NETWORK
    )

    # Initialize configuration
    print("Initializing Incident Copilot...\n")

    config = RAGConfig(
        index_name="incident-reports",
        model="models/gemini-2.0-flash",
        embedding_model="models/text-embedding-004",
        embedding_dimension=768
    )

    # Create copilot
    copilot = IncidentCopilot(config)

    # # Visualize the graph workflow
    # print("\n" + "="*60)
    # print("VISUALIZING WORKFLOW GRAPH")
    # print("="*60)
    # copilot.visualize_graph(output_path="incident_copilot_graph.png")
    #
    # # Example 1: Complete Incident Report - CAN Bus DoS Attack
    # print("\n" + "="*60)
    # print("EXAMPLE 1: Complete Incident Report (Full Path)")
    # print("="*60)
    #
    # result1 = copilot.process(
    #     incident_report=COMPLETE_REPORT_CAN_BUS,
    #     verbose=True
    # )
    #
    # # Example 2: Complete Incident Report - GPS Spoofing Attack
    # print("\n" + "="*60)
    # print("EXAMPLE 2: Complete Incident Report (Full Path)")
    # print("="*60)
    #
    # result2 = copilot.process(
    #     incident_report=COMPLETE_REPORT_GPS_SPOOFING,
    #     verbose=True
    # )

    # Example 3: Incomplete/Noisy Incident Report - Missing Critical Info
    print("\n" + "="*60)
    print("EXAMPLE 3: Incomplete Incident Report (Conservative Path)")
    print("="*60)

    result3 = copilot.process(
        incident_report=INCOMPLETE_REPORT_SUSPICIOUS_NETWORK,
        verbose=True
    )


if __name__ == "__main__":
    main()