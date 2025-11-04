"""
Validation Node - Extracts standard information from incident reports.
Uses the Validation Agent to extract WHO, WHAT, WHERE, WHEN, IMPACT, STATUS.
"""

import re
from typing import Dict, Any
import google.generativeai as genai

from .base_node import BaseNode
from system_prompts import MITIGATION_AGENT_PROMPT


class CompleteMitigationNode(BaseNode):
    """Validates input and extracts standard information using Validation Agent."""

    def __init__(self, config):
        """
        Initialize validation node.

        Args:
            config: RAG configuration object
        """
        super().__init__(config)
        self.mitigation_system_message = MITIGATION_AGENT_PROMPT

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates mitigation plan using Mitigation Agent with retrieved historical context.

        Args:
            state: Current workflow state

        Returns:
            Updated state with mitigation plan
        """
        try:
            print(f"\n[Mitigation Agent] Generating mitigation strategy...")

            # Build context from retrieved similar incidents
            if state['retrieved_incidents']:
                similar_incidents_context = "\n\n".join([
                    f"**Incident {inc['incident_id']}** ({inc['metadata'].get('threat_category', 'Unknown')}):\n{inc['description']}"
                    for inc in state['retrieved_incidents'][:3]
                ])
            else:
                similar_incidents_context = ""

            # Build context from retrieved recommendations
            if state['retrieved_recommendations']:
                recommendations_context = "\n\n".join([
                    f"- {rec}"
                    for rec in state['retrieved_recommendations'][:5]
                ])
            else:
                recommendations_context = "No past recommendations available."

            # Human message with incident summary and retrieved context
            human_message = f"""Please generate a mitigation plan for this incident.

            **CURRENT INCIDENT SUMMARY:**
            {state['summary']}
            
            **SIMILAR HISTORICAL INCIDENTS (Descriptions):**
            {similar_incidents_context}
            
            **RECOMMENDATIONS FROM SIMILAR INCIDENTS:**
            {recommendations_context}
            
            Please provide a comprehensive mitigation plan based on the above information."""

            # Call Mitigation Agent with system/human messages
            response = self.config.gemini_model.generate_content(
                [
                    {'role': 'user', 'parts': [self.mitigation_system_message]},
                    {'role': 'model', 'parts': ['I understand. I will generate comprehensive, actionable mitigation and response strategies based on the incident summary and historical context.']},
                    {'role': 'user', 'parts': [human_message]}
                ],
                generation_config=genai.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=1000
                )
            )

            state['mitigation_plan'] = response.text.strip()

            # Format final response: Summary + Mitigation Plan + Context Info
            context_info = ""
            if state['retrieved_incidents']:
                context_info = f"""
                
                ---
                **Analysis Context**
                Mitigation plan based on {len(state['retrieved_incidents'])} similar historical incident(s):
                {chr(10).join([f"- **{inc['incident_id']}**: {inc['metadata'].get('threat_category', 'N/A')} (Similarity: {inc.get('score', 0):.2f})"
               for inc in state['retrieved_incidents'][:3]])}
            """

            state['final_response'] = f"""## Incident Summary

            {state['summary']}
            
            ---
            
            ## Mitigation Plan
            
            {state['mitigation_plan']}{context_info}"""

            print(f"[Mitigation Agent] Plan generated ({len(state['mitigation_plan'])} chars)")

        except Exception as e:
            state['error'] = f"Error in mitigation: {str(e)}"
            state['final_response'] = f"Error generating mitigation plan: {str(e)}"
            print(f"[Mitigation Agent] Error: {e}")

        return state