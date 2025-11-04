"""
Validation Node - Extracts standard information from incident reports.
Uses the Validation Agent to extract WHO, WHAT, WHERE, WHEN, IMPACT, STATUS.
"""

from typing import Dict, Any
import google.generativeai as genai

from .base_node import BaseNode
from configs.system_prompts import CONSERVATIVE_SUMMARY_AGENT_PROMPT


class ConservativeSummaryNode(BaseNode):
    """Validates input and extracts standard information using Validation Agent."""

    def __init__(self, config):
        """
        Initialize validation node.

        Args:
            config: RAG configuration object
        """
        super().__init__(config)
        self.conservative_summary_system_message = CONSERVATIVE_SUMMARY_AGENT_PROMPT

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates conservative summary when critical information is missing.

        Args:
            state: Current workflow state

        Returns:
            Updated state with conservative summary
        """
        try:
            print(f"\n[Conservative Summary Agent] Generating faithful summary (critical info missing)...")

            incident_report = state['incident_report']

            # Human message requesting conservative summary
            human_message = f"Please provide a conservative summary of this incident report. Critical information is missing:\n\n{incident_report}"

            # Call Conservative Summary Agent with system/human messages
            response = self.config.gemini_model.generate_content(
                [
                    {'role': 'user', 'parts': [self.conservative_summary_system_message]},
                    {'role': 'model', 'parts': ['I understand. I will provide a faithful, conservative summary based ONLY on what is explicitly stated in the report, and clearly identify missing critical information.']},
                    {'role': 'user', 'parts': [human_message]}
                ],
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=300
                )
            )

            state['summary'] = response.text.strip()

            print(f"[Conservative Summary Agent] Summary generated ({len(state['summary'])} chars)")

        except Exception as e:
            state['error'] = f"Error in conservative summary: {str(e)}"
            state['summary'] = f"Error generating conservative summary: {str(e)}"
            print(f"[Conservative Summary Agent] Error: {e}")

        return state
