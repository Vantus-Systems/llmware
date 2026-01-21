
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
from llmware.parsers.utils import process_parser_output
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

        blocks = process_parser_output(output_file_path)

        # Update file_type if needed (util sets to 'unknown')
        for b in blocks:
            b.file_type = "pdf"

        # Cleanup
        try:
            if output_file_path.exists():
                output_file_path.unlink()
        except OSError as e:
            logger.warning(f"Could not delete temp file {output_file_path}: {e}")

        return blocks
