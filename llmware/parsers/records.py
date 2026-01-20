from dataclasses import dataclass, field
from typing import Dict, Optional, Any, List

@dataclass
class Block:
    """Standardized data class representing a parsed block of content."""

    text: str
    doc_id: int = 0
    block_id: int = 0
    file_source: str = ""
    content_type: str = "text"
    file_type: str = "text"
    master_index: int = 0
    master_index2: int = 0
    coords_x: int = 0
    coords_y: int = 0
    coords_cx: int = 0
    coords_cy: int = 0
    author_or_speaker: str = ""
    modified_date: str = ""
    created_date: str = ""
    creator_tool: str = ""
    added_to_collection: str = ""
    table: str = ""
    external_files: str = ""
    header_text: str = ""
    text_search: str = ""
    user_tags: str = ""
    special_field1: str = ""
    special_field2: str = ""
    special_field3: str = ""
    graph_status: str = "false"
    dialog: str = "false"
    embedding_flags: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Converts the Block to a dictionary."""
        return {
            "block_ID": self.block_id,
            "doc_ID": self.doc_id,
            "content_type": self.content_type,
            "file_type": self.file_type,
            "master_index": self.master_index,
            "master_index2": self.master_index2,
            "coords_x": self.coords_x,
            "coords_y": self.coords_y,
            "coords_cx": self.coords_cx,
            "coords_cy": self.coords_cy,
            "author_or_speaker": self.author_or_speaker,
            "modified_date": self.modified_date,
            "created_date": self.created_date,
            "creator_tool": self.creator_tool,
            "added_to_collection": self.added_to_collection,
            "file_source": self.file_source,
            "table": self.table,
            "external_files": self.external_files,
            "text": self.text,
            "header_text": self.header_text,
            "text_search": self.text_search,
            "user_tags": self.user_tags,
            "special_field1": self.special_field1,
            "special_field2": self.special_field2,
            "special_field3": self.special_field3,
            "graph_status": self.graph_status,
            "dialog": self.dialog,
            "embedding_flags": self.embedding_flags
        }
