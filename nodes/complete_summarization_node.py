"""
Validation Node - Extracts standard information from incident reports.
Uses the Validation Agent to extract WHO, WHAT, WHERE, WHEN, IMPACT, STATUS.
"""

from typing import Dict, Any
import google.generativeai as genai

from .base_node import BaseNode
from configs.system_prompts import SUMMARIZATION_AGENT_PROMPT


class CompleteSummarizationNode(BaseNode):
    """Validates input and extracts standard information using Validation Agent."""

    def __init__(self, config):
        """
        Initialize validation node.

        Args:
            config: RAG configuration object
        """
        super().__init__(config)
        self.summarization_system_message = SUMMARIZATION_AGENT_PROMPT

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates concise summary of the provided incident report using Summarization Agent.

        Args:
            state: Current workflow state

        Returns:
            Updated state with summary
        """
        try:
            print(f"\n[Summarization Agent] Generating summary...")

            # Use the incident report provided by the user
            incident_report = state['incident_report']

            # Human message requesting summary
            human_message = f"Please provide a summary of this incident report:\n\n{incident_report}"

            # Call Summarization Agent with system/human messages
            response = self.config.gemini_model.generate_content(
                [
                    {'role': 'user', 'parts': [self.summarization_system_message]},
                    {'role': 'model', 'parts': ['I understand. I will provide concise, executive-level summaries of security incidents following the specified format.']},
                    {'role': 'user', 'parts': [human_message]}
                ],
                generation_config=genai.GenerationConfig(
                    temperature=0.5,
                    max_output_tokens=300
                )
            )

            state['summary'] = response.text.strip()

            print(f"[Summarization Agent] Summary generated ({len(state['summary'])} chars)")

        except Exception as e:
            state['error'] = f"Error in summarization: {str(e)}"
            state['summary'] = f"Error generating summary: {str(e)}"
            print(f"[Summarization Agent] Error: {e}")

        return state