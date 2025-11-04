"""
Validation Node - Extracts standard information from incident reports.
Uses the Validation Agent to extract WHO, WHAT, WHERE, WHEN, IMPACT, STATUS.
"""

import re
from typing import Dict, Any
import google.generativeai as genai

from .base_node import BaseNode
from system_prompts import CONSERVATIVE_NEXTSTEPS_AGENT_PROMPT


class ConservativeNextStepsNode(BaseNode):
    """Validates input and extracts standard information using Validation Agent."""

    def __init__(self, config):
        """
        Initialize validation node.

        Args:
            config: RAG configuration object
        """
        super().__init__(config)
        self.conservative_nextsteps_system_message = CONSERVATIVE_NEXTSTEPS_AGENT_PROMPT

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates conservative next steps when critical information is missing.

        Args:
            state: Current workflow state

        Returns:
            Updated state with conservative next steps
        """
        try:
            print(f"\n[Conservative Next Steps Agent] Generating basic precautionary steps...")

            # Human message requesting conservative next steps
            human_message = f"""Please provide conservative next steps for this incident.

            **Current Summary:**
            {state['summary']}
            
            **Missing Information:**
            - Timeline: {'Missing' if state['when'].lower() in ['unknown', 'not specified'] else 'Available'}
            - Impact Assessment: {'Missing' if state['impact'].lower() in ['unknown', 'not specified'] else 'Available'}
            
            Provide VERY CONSERVATIVE recommendations focusing on information gathering and basic precautionary measures."""

            # Call Conservative Next Steps Agent with system/human messages
            response = self.config.gemini_model.generate_content(
                [
                    {'role': 'user', 'parts': [self.conservative_nextsteps_system_message]},
                    {'role': 'model', 'parts': ['I understand. I will provide conservative, cautious next steps focused on information gathering and basic precautionary measures. This is NOT a full mitigation plan.']},
                    {'role': 'user', 'parts': [human_message]}
                ],
                generation_config=genai.GenerationConfig(
                    temperature=0.4,
                    max_output_tokens=500
                )
            )

            conservative_nextsteps = response.text.strip()

            # Format final response for conservative path
            state['final_response'] = f"""## Incident Summary (Limited Information Available)

            {state['summary']}
            
            ---
            
            ## Conservative Next Steps
            
            ⚠️ **Note:** Critical information is missing from this report. Full mitigation planning requires complete information about timeline and/or impact.
            
            {conservative_nextsteps}"""

            # Set mitigation_plan to empty or a note for conservative path
            state['mitigation_plan'] = "(Conservative path - full mitigation plan not generated due to missing critical information)"

            print(f"[Conservative Next Steps Agent] Next steps generated ({len(conservative_nextsteps)} chars)")

        except Exception as e:
            state['error'] = f"Error in conservative next steps: {str(e)}"
            state['final_response'] = f"Error generating conservative next steps: {str(e)}"
            print(f"[Conservative Next Steps Agent] Error: {e}")

        return state