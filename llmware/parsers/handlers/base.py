
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import logging

from llmware.parsers.records import Block

logger = logging.getLogger(__name__)

class BaseHandler(ABC):
    """Abstract base class for all document handlers."""

    def __init__(self, parser_state: Any = None):
        """
        Args:
            parser_state: The main Parser object, acting as the context/orchestrator.
                          Used to access shared resources like library, config, etc.
        """
        self.parser = parser_state

    @abstractmethod
    def parse(self, input_path: Union[str, Path], filename: str, **kwargs) -> List[Block]:
        """
        Parses a single file and returns a list of Blocks.

        Args:
            input_path: The directory path containing the file.
            filename: The name of the file to parse.
            **kwargs: Additional parsing arguments.

        Returns:
            List[Block]: A list of parsed blocks.
        """
        pass

    def _create_block(self, text: str, **kwargs) -> Block:
        """Helper to create a Block with default values populated from context if available."""
        # Logic to populate defaults from self.parser if needed
        return Block(text=text, **kwargs)

    @property
    def supported_extensions(self) -> List[str]:
        """Returns a list of supported file extensions."""
        return []
