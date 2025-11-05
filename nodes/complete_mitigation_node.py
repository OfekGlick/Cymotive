"""
Validation Node - Extracts standard information from incident reports.
Uses the Validation Agent to extract WHO, WHAT, WHERE, WHEN, IMPACT, STATUS.
"""

from typing import Dict, Any
import google.generativeai as genai

from .base_node import BaseNode
from configs.system_prompts import MITIGATION_AGENT_PROMPT


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

            # Build few-shot examples from retrieved similar incidents
            # Each example contains both the incident description and its mitigation recommendations
            if state['retrieved_incidents']:
                few_shot_examples = "\n\n".join([
                    f"""### Example {i}: {inc['incident_id']} ({inc['metadata'].get('threat_category', 'Unknown')})
**Incident Description:**
{inc['description']}

**Mitigation Strategy:**
{inc['recommendations']}"""
                    for i, inc in enumerate(state['retrieved_incidents'][:3], 1)
                ])
            else:
                few_shot_examples = "No similar historical incidents available."

            # Human message with incident summary and few-shot examples
            human_message = f"""Please generate a mitigation plan for this incident.

            **CURRENT INCIDENT SUMMARY:**
            {state['summary']}

            **FEW-SHOT EXAMPLES FROM SIMILAR HISTORICAL INCIDENTS:**
            Below are examples of similar incidents and how they were mitigated. Use these as reference to create a comprehensive mitigation plan for the current incident.

            {few_shot_examples}

            Based on the current incident summary and the few-shot examples above, please provide a comprehensive mitigation plan."""

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