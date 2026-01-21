
import os
import json
import logging
from pathlib import Path
from typing import List, Any, Union

from llmware.util import TextChunker
from llmware.parsers.handlers.base import BaseHandler
from llmware.parsers.records import Block
from llmware.exceptions import FilePathDoesNotExistException

logger = logging.getLogger(__name__)

class TextHandler(BaseHandler):
    """Handler for Text documents (TXT, MD, CSV, JSON, JSONL)."""

    @property
    def supported_extensions(self) -> List[str]:
        return ["txt", "md", "csv", "tsv", "json", "jsonl"]

    def parse(self, input_path: Union[str, Path], filename: str, **kwargs) -> List[Block]:
        input_path = Path(input_path)
        if not (input_path / filename).exists():
            raise FilePathDoesNotExistException(str(input_path / filename))

        chunk_size = kwargs.get("chunk_size", 400)
        file_path = input_path / filename
        ext = filename.split(".")[-1].lower()

        blocks = []

        if ext in ["txt", "md"]:
            blocks = self._parse_text_file(file_path, chunk_size)
        elif ext in ["csv", "tsv"]:
            # Basic CSV handling
            blocks = self._parse_csv_file(file_path, chunk_size, separator="\t" if ext == "tsv" else ",")
        elif ext in ["json", "jsonl"]:
            blocks = self._parse_jsonl_file(file_path)

        # Enrich blocks with metadata
        for i, block in enumerate(blocks):
            block.file_source = filename
            block.file_type = ext
            block.doc_id = kwargs.get("doc_id", 0)
            block.block_id = i

        return blocks

    def _parse_text_file(self, file_path: Path, chunk_size: int) -> List[Block]:
        try:
            text = file_path.read_text(encoding="utf-8-sig", errors="ignore")
        except Exception as e:
            logger.error(f"Error reading text file: {e}")
            return []

        chunks = TextChunker(text_chunk=text, max_char_size=chunk_size).convert_text_to_chunks()
        return [Block(text=c) for c in chunks]

    def _parse_csv_file(self, file_path: Path, chunk_size: int, separator: str = ",") -> List[Block]:
        # Simple implementation
        try:
            text = file_path.read_text(encoding="utf-8-sig", errors="ignore")
        except:
            return []

        # Treat as text for now, or split by lines
        lines = text.split("\n")
        blocks = []
        for line in lines:
            if line.strip():
                blocks.append(Block(text=line, content_type="table"))
        return blocks

    def _parse_jsonl_file(self, file_path: Path) -> List[Block]:
        blocks = []
        try:
            with open(file_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                if file_path.suffix == ".json":
                    data = json.load(f)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict):
                                blocks.append(Block(text=str(item)))
                    elif isinstance(data, dict):
                        blocks.append(Block(text=str(data)))
                else:
                    for line in f:
                        if line.strip():
                            try:
                                row = json.loads(line)
                                blocks.append(Block(text=str(row)))
                            except:
                                pass
        except:
            pass
        return blocks
