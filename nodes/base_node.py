"""
Base Node Class for Incident Copilot Workflow.
Provides common interface and utilities for all workflow nodes.
"""

from typing import Dict, Any
from abc import ABC, abstractmethod


class BaseNode(ABC):
    """Base class for all workflow nodes."""

    def __init__(self, config):
        """
        Initialize base node.

        Args:
            config: RAG configuration object
        """
        self.config = config

    @abstractmethod
    def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the node logic.

        Args:
            state: Current workflow state

        Returns:
            Updated state
        """
        pass

    def __call__(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Make node callable for LangGraph."""
        return self.execute(state)