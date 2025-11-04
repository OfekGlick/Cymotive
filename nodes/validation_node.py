"""
Validation Node - Extracts standard information from incident reports.
Uses the Validation Agent to extract WHO, WHAT, WHERE, WHEN, IMPACT, STATUS.
"""

import re
from typing import Dict, Any
import google.generativeai as genai

from .base_node import BaseNode
from system_prompts import VALIDATION_AGENT_PROMPT


class ValidationNode(BaseNode):
    """Validates input and extracts standard information using Validation Agent."""

    def __init__(self, config):
        """
        Initialize validation node.

        Args:
            config: RAG configuration object
        """
        super().__init__(config)
        self.system_message = VALIDATION_AGENT_PROMPT

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates input and extracts standard information.

        Args:
            state: Current workflow state

        Returns:
            Updated state with extracted information and validation flags
        """
        try:
            print(f"\n[Validation Agent] Extracting standard information...")

            incident_report = state['incident_report']

            # Human message requesting information extraction
            human_message = f"Please extract the standard information from this incident report:\n\n{incident_report}"

            # Call Validation Agent with system/human messages
            response = self.config.gemini_model.generate_content(
                [
                    {'role': 'user', 'parts': [self.system_message]},
                    {'role': 'model', 'parts': ['I understand. I will extract WHO, WHAT, WHERE, WHEN, IMPACT, and STATUS information from the incident report.']},
                    {'role': 'user', 'parts': [human_message]}
                ],
                generation_config=genai.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=500
                )
            )

            # Parse the response to extract each field
            response_text = response.text.strip()
            self._parse_and_update_state(state, response_text)

            # Check if critical information is missing
            when_missing = state['when'].lower() in ['unknown', 'not specified', '']
            impact_missing = state['impact'].lower() in ['unknown', 'not specified', '']
            state['critical_info_missing'] = when_missing or impact_missing

            # Also extract description for retrieval (use 'what' as description if present)
            state['description'] = state['what'] if state['what'] != "Unknown" else incident_report[:500]

            self._print_extracted_info(state)

        except Exception as e:
            state['error'] = f"Error in validation: {str(e)}"
            self._set_default_values(state)
            print(f"[Validation Agent] Error: {e}")

        return state

    def _parse_and_update_state(self, state: Dict[str, Any], response_text: str):
        """Parse LLM response and update state with extracted fields."""
        who_match = re.search(r'WHO:\s*(.+?)(?=\nWHAT:|\nWHERE:|\n\n|$)', response_text, re.DOTALL)
        what_match = re.search(r'WHAT:\s*(.+?)(?=\nWHERE:|\nWHEN:|\n\n|$)', response_text, re.DOTALL)
        where_match = re.search(r'WHERE:\s*(.+?)(?=\nWHEN:|\nIMPACT:|\n\n|$)', response_text, re.DOTALL)
        when_match = re.search(r'WHEN:\s*(.+?)(?=\nIMPACT:|\nSTATUS:|\n\n|$)', response_text, re.DOTALL)
        impact_match = re.search(r'IMPACT:\s*(.+?)(?=\nSTATUS:|\n\n|$)', response_text, re.DOTALL)
        status_match = re.search(r'STATUS:\s*(.+?)(?=\n\n|$)', response_text, re.DOTALL)

        state['who'] = who_match.group(1).strip() if who_match else "Unknown"
        state['what'] = what_match.group(1).strip() if what_match else "Unknown"
        state['where'] = where_match.group(1).strip() if where_match else "Unknown"
        state['when'] = when_match.group(1).strip() if when_match else "Unknown"
        state['impact'] = impact_match.group(1).strip() if impact_match else "Unknown"
        state['status'] = status_match.group(1).strip() if status_match else "Unknown"

    def _set_default_values(self, state: Dict[str, Any]):
        """Set default values when extraction fails."""
        state['who'] = "Unknown"
        state['what'] = "Unknown"
        state['where'] = "Unknown"
        state['when'] = "Unknown"
        state['impact'] = "Unknown"
        state['status'] = "Unknown"
        state['critical_info_missing'] = True
        state['description'] = state['incident_report'][:500]

    def _print_extracted_info(self, state: Dict[str, Any]):
        """Print extracted information for debugging."""
        print(f"[Validation Agent] Extracted information:")
        print(f"  WHO: {state['who'][:50]}...")
        print(f"  WHAT: {state['what'][:50]}...")
        print(f"  WHERE: {state['where'][:50]}...")
        print(f"  WHEN: {state['when'][:50]}...")
        print(f"  IMPACT: {state['impact'][:50]}...")
        print(f"  STATUS: {state['status'][:50]}...")
        print(f"  Critical info missing: {state['critical_info_missing']}")