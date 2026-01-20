
import os
import time
import ctypes
from ctypes import create_string_buffer, c_int, c_char_p
from pathlib import Path
from typing import List, Dict, Any, Union
import logging

from llmware.configs import LLMWareConfig
from llmware.parsers.handlers.base import BaseHandler
from llmware.parsers.records import Block
from llmware.parsers.bindings import ParserBindings, DebugMode, ImageSaveMode, EncodingStyle, TableExtractMode
from llmware.exceptions import FilePathDoesNotExistException, LLMWareException

logger = logging.getLogger(__name__)

class PDFHandler(BaseHandler):
    """Handler for PDF documents using C-based parser."""

    def __init__(self, parser_state: Any = None):
        super().__init__(parser_state)
        self.bindings = ParserBindings()

    @property
    def supported_extensions(self) -> List[str]:
        return ["pdf"]

    def parse(self, input_path: Union[str, Path], filename: str, **kwargs) -> List[Block]:
        """
        Parses a single PDF file.

        Args:
            input_path: Directory path.
            filename: Filename.
            **kwargs: Configuration overrides.
        """
        input_path = Path(input_path)
        if not (input_path / filename).exists():
            raise FilePathDoesNotExistException(str(input_path / filename))

        # Check if library is loaded
        if not self.bindings.lib_pdf:
            raise LLMWareException("PDF Parser library not loaded.")

        # Configuration (defaults from parser_state or kwargs)
        chunk_size = kwargs.get("chunk_size", 400)
        max_chunk_size = kwargs.get("max_chunk_size", 600)
        smart_chunking = kwargs.get("smart_chunking", 1)
        verbose_level = kwargs.get("verbose_level", 2)
        get_images = kwargs.get("get_images", True)
        get_tables = kwargs.get("get_tables", True)
        get_header_text = kwargs.get("get_header_text", True)
        strip_header = kwargs.get("strip_header", False)
        table_strategy = kwargs.get("table_strategy", 1)
        encoding = kwargs.get("encoding", "utf-8")

        # Prepare C arguments
        account_name = getattr(self.parser, "account_name", "llmware")
        library_name = getattr(self.parser, "library_name", "default")

        # Paths
        fp_c = create_string_buffer(str(input_path).encode('utf-8'))
        fn_c = create_string_buffer(filename.encode('utf-8'))

        # Output paths (using temp folder)
        tmp_path = Path(LLMWareConfig.get_tmp_path())
        if not tmp_path.exists():
            tmp_path.mkdir(parents=True, exist_ok=True)

        parser_tmp_folder = tmp_path / "parser_tmp"
        if not parser_tmp_folder.exists():
            parser_tmp_folder.mkdir(parents=True, exist_ok=True)

        # Image path (if getting images)
        if hasattr(self.parser, "parser_image_folder") and self.parser.parser_image_folder:
            image_fp = Path(self.parser.parser_image_folder)
        else:
            image_fp = parser_tmp_folder

        if not image_fp.exists():
            image_fp.mkdir(parents=True, exist_ok=True)

        image_fp_str = str(image_fp)
        if not image_fp_str.endswith(os.sep):
            image_fp_str += os.sep
        image_fp_c = create_string_buffer(image_fp_str.encode('utf-8'))

        # Output filename for the C parser text dump
        write_to_filename = f"pdf_out_{int(time.time())}.txt"
        write_to_filename_c = create_string_buffer(write_to_filename.encode('utf-8'))

        # Flags and Enums
        user_block_size_c = c_int(chunk_size)
        unique_doc_num_c = c_int(kwargs.get("doc_id", 1))

        strip_header_c = c_int(1) if strip_header else c_int(0)

        table_extract_c = c_int(0)
        if get_tables:
            if 0 <= table_strategy <= 2:
                table_extract_c = c_int(table_strategy)
            else:
                table_extract_c = c_int(1)

        smart_chunking_c = c_int(smart_chunking)
        max_chunk_size_c = c_int(max_chunk_size)

        encoding_style_c = c_int(EncodingStyle.UTF_8)
        if encoding == "ascii":
            encoding_style_c = c_int(EncodingStyle.ASCII)
        elif encoding == "latin-1":
            encoding_style_c = c_int(EncodingStyle.LATIN_1)

        get_header_text_c = c_int(1) if get_header_text else c_int(0)
        table_grid_c = c_int(1) # Defaulting to 1 as per original code seems common

        save_images_c = c_int(ImageSaveMode.ON) if get_images else c_int(ImageSaveMode.OFF)

        # Logger config
        logger_level_c = c_int(40) # Default to error only unless debug
        if verbose_level > 0:
             logger_level_c = c_int(20) # Info

        # Log file
        parser_folder = Path(LLMWareConfig.get_parser_path())
        log_file_path = parser_folder / "parser_log.txt"
        debug_log_file_c = create_string_buffer(str(log_file_path).encode('utf-8'))

        input_debug_mode_c = c_int(DebugMode.OFF)
        if kwargs.get("use_logging_file", False):
            input_debug_mode_c = c_int(DebugMode.FILE_LOGGING)

        # C Account/Lib buffers
        account_name_c = create_string_buffer(account_name.encode('utf-8'))
        library_name_c = create_string_buffer(library_name.encode('utf-8'))

        logger.info(f"PDFHandler - Parsing {filename} in {input_path}")

        # Call C function
        # add_one_pdf_opts(account, lib, path, filename, image_path, write_to, block_size, doc_num, ...)

        try:
            result = self.bindings.lib_pdf.add_one_pdf_opts(
                account_name_c,
                library_name_c,
                fp_c,
                fn_c,
                image_fp_c,
                write_to_filename_c,
                user_block_size_c,
                unique_doc_num_c,
                strip_header_c,
                table_extract_c,
                smart_chunking_c,
                max_chunk_size_c,
                encoding_style_c,
                get_header_text_c,
                table_grid_c,
                save_images_c,
                logger_level_c,
                debug_log_file_c,
                input_debug_mode_c
            )
        except Exception as e:
            logger.error(f"Error calling C PDF parser: {e}")
            raise LLMWareException(f"C Parser Error: {e}")

        # Process output file
        output_file_path = parser_tmp_folder / write_to_filename

        blocks = self._process_parser_output(output_file_path)

        # Cleanup
        try:
            if output_file_path.exists():
                output_file_path.unlink()
        except OSError as e:
            logger.warning(f"Could not delete temp file {output_file_path}: {e}")

        return blocks

    def _process_parser_output(self, file_path: Path) -> List[Block]:
        """Reads the text file output from C parser and converts to Blocks."""

        if not file_path.exists():
            logger.warning(f"Parser output file not found: {file_path}")
            return []

        default_keys = [
            "block_ID", "doc_ID", "content_type", "file_type", "master_index", "master_index2",
            "coords_x", "coords_y", "coords_cx", "coords_cy", "author_or_speaker", "modified_date",
            "created_date", "creator_tool", "added_to_collection", "file_source",
            "table", "external_files", "text", "header_text", "text_search",
            "user_tags", "special_field1", "special_field2", "special_field3", "graph_status", "dialog"
        ]

        blocks: List[Block] = []

        try:
            with open(file_path, "r", encoding="utf-8-sig", errors="ignore") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Error reading parser output file: {e}")
            return []

        # Split by the C-parser defined delimiter
        raw_blocks = content.split("<END_BLOCK>\n")

        for raw_block in raw_blocks:
            if not raw_block.strip():
                continue

            block_data = {}
            lines = raw_block.split("\n<")

            for line in lines:
                for key in default_keys:
                    key_marker = f"{key}>: "
                    # Check if line starts with key marker (handling the first line which might not have \n< prefix effectively in split)
                    # The split removed \n<, so lines usually start with KEY>:
                    # But the first line of raw_block might be just KEY>: if it was at start of file?
                    # The original parser code: entries.startswith(key_string)

                    if line.startswith(key_marker) or line.startswith(f"<{key_marker}"):
                        # Clean up the key marker
                        clean_marker = key_marker
                        if line.startswith("<"):
                             clean_marker = f"<{key_marker}"

                        value = line[len(clean_marker):].strip()
                        if value.endswith(","):
                            value = value[:-1]

                        block_data[key] = value
                        break

            # Map to Block dataclass
            if "text" in block_data:
                # Convert numeric fields
                try:
                    doc_id = int(block_data.get("doc_ID", 0))
                except: doc_id = 0

                try:
                    block_id = int(block_data.get("block_ID", 0))
                except: block_id = 0

                try:
                    coords_x = int(block_data.get("coords_x", 0))
                except: coords_x = 0

                try:
                    coords_y = int(block_data.get("coords_y", 0))
                except: coords_y = 0

                # ... map other fields ...

                block = Block(
                    text=block_data.get("text", ""),
                    doc_id=doc_id,
                    block_id=block_id,
                    file_source=block_data.get("file_source", ""),
                    content_type=block_data.get("content_type", "text"),
                    file_type=block_data.get("file_type", "pdf"),
                    master_index=int(block_data.get("master_index", 0)) if block_data.get("master_index", "").isdigit() else 0,
                    master_index2=int(block_data.get("master_index2", 0)) if block_data.get("master_index2", "").isdigit() else 0,
                    coords_x=coords_x,
                    coords_y=coords_y,
                    coords_cx=int(block_data.get("coords_cx", 0)) if block_data.get("coords_cx", "").isdigit() else 0,
                    coords_cy=int(block_data.get("coords_cy", 0)) if block_data.get("coords_cy", "").isdigit() else 0,
                    author_or_speaker=block_data.get("author_or_speaker", ""),
                    modified_date=block_data.get("modified_date", ""),
                    created_date=block_data.get("created_date", ""),
                    creator_tool=block_data.get("creator_tool", ""),
                    added_to_collection=block_data.get("added_to_collection", ""),
                    table=block_data.get("table", ""),
                    external_files=block_data.get("external_files", ""),
                    header_text=block_data.get("header_text", ""),
                    text_search=block_data.get("text_search", ""),
                    user_tags=block_data.get("user_tags", ""),
                    special_field1=block_data.get("special_field1", ""),
                    special_field2=block_data.get("special_field2", ""),
                    special_field3=block_data.get("special_field3", ""),
                    graph_status=block_data.get("graph_status", "false"),
                    dialog=block_data.get("dialog", "false")
                )
                blocks.append(block)

        return blocks
