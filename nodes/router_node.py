"""
Router Node - Checks critical information status and logs routing decision.
Simple logging node that prepares for conditional routing.
"""

from typing import Dict, Any

from .base_node import BaseNode


class RouterNode(BaseNode):
    """Router node that checks critical info and prepares for routing."""

    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check critical information status and log routing decision.

        Args:
            state: Current workflow state

        Returns:
            State (unchanged, routing happens via conditional edges)
        """
        print(f"\n[Router] Checking critical information status...")
        print(f"[Router] Critical info missing: {state['critical_info_missing']}")

        if state['critical_info_missing']:
            print(f"[Router] Routing to CONSERVATIVE path (limited summary + basic next steps)")
        else:
            print(f"[Router] Routing to FULL path (complete summary + mitigation plan)")

        return state