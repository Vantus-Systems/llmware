
import os
import time
import logging
from ctypes import create_string_buffer, c_int
from pathlib import Path
from typing import List, Any, Union

from llmware.configs import LLMWareConfig
from llmware.parsers.handlers.base import BaseHandler
from llmware.parsers.records import Block
from llmware.parsers.bindings import ParserBindings, DebugMode, ImageSaveMode, EncodingStyle, TableExtractMode
from llmware.parsers.utils import process_parser_output
from llmware.exceptions import FilePathDoesNotExistException, LLMWareException

logger = logging.getLogger(__name__)

class OfficeHandler(BaseHandler):
    """Handler for Office documents (DOCX, PPTX, XLSX) using C-based parser."""

    def __init__(self, parser_state: Any = None):
        super().__init__(parser_state)
        self.bindings = ParserBindings()

    @property
    def supported_extensions(self) -> List[str]:
        return ["docx", "doc", "pptx", "ppt", "xlsx", "xls"]

    def parse(self, input_path: Union[str, Path], filename: str, **kwargs) -> List[Block]:
        """
        Parses a single Office file.
        """
        input_path = Path(input_path)
        if not (input_path / filename).exists():
            raise FilePathDoesNotExistException(str(input_path / filename))

        if not self.bindings.lib_office:
            raise LLMWareException("Office Parser library not loaded.")

        # Configuration
        chunk_size = kwargs.get("chunk_size", 400)
        max_chunk_size = kwargs.get("max_chunk_size", 600)
        smart_chunking = kwargs.get("smart_chunking", 1)
        verbose_level = kwargs.get("verbose_level", 2)
        get_images = kwargs.get("get_images", True)
        get_tables = kwargs.get("get_tables", True)
        get_header_text = kwargs.get("get_header_text", True)
        strip_header = kwargs.get("strip_header", False)
        encoding = kwargs.get("encoding", "utf-8")

        # Prepare C arguments
        account_name = getattr(self.parser, "account_name", "llmware")
        library_name = getattr(self.parser, "library_name", "default")

        fp_c = create_string_buffer(str(input_path).encode('utf-8'))
        fn_c = create_string_buffer(filename.encode('utf-8'))

        # Output workspace
        tmp_path = Path(LLMWareConfig.get_tmp_path())
        parser_tmp_folder = tmp_path / "parser_tmp"
        if not parser_tmp_folder.exists():
            parser_tmp_folder.mkdir(parents=True, exist_ok=True)

        workspace_fp_c = create_string_buffer(str(parser_tmp_folder).encode('utf-8'))

        # Set up subfolders in workspace as expected by C parser (0, 1, 2...)
        # parse_office logic loops range(0,5)
        # parse_one_office logic loops range(0,1)
        if not (parser_tmp_folder / "0").exists():
            (parser_tmp_folder / "0").mkdir(exist_ok=True)

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

        write_to_filename = f"office_out_{int(time.time())}.txt"
        write_to_filename_c = create_string_buffer(write_to_filename.encode('utf-8'))

        user_block_size_c = c_int(chunk_size)
        unique_doc_num_c = c_int(kwargs.get("doc_id", 1))

        strip_header_c = c_int(1) if strip_header else c_int(0)
        table_extract_c = c_int(1) if get_tables else c_int(0)
        smart_chunking_c = c_int(smart_chunking)
        max_chunk_size_c = c_int(max_chunk_size)

        encoding_style_c = c_int(EncodingStyle.UTF_8)
        if encoding == "ascii":
            encoding_style_c = c_int(EncodingStyle.ASCII)

        get_header_text_c = c_int(1) if get_header_text else c_int(0)
        table_grid_c = c_int(1) # Default

        save_images_c = c_int(ImageSaveMode.ON) if get_images else c_int(ImageSaveMode.OFF)

        logger_level_c = c_int(40)
        if verbose_level > 0:
             logger_level_c = c_int(20)

        parser_folder = Path(LLMWareConfig.get_parser_path())
        log_file_path = parser_folder / "parser_log.txt"
        debug_log_file_c = create_string_buffer(str(log_file_path).encode('utf-8'))

        input_debug_mode_c = c_int(DebugMode.OFF)
        if kwargs.get("use_logging_file", False):
            input_debug_mode_c = c_int(DebugMode.FILE_LOGGING)

        account_name_c = create_string_buffer(account_name.encode('utf-8'))
        library_name_c = create_string_buffer(library_name.encode('utf-8'))

        logger.info(f"OfficeHandler - Parsing {filename}")

        try:
            self.bindings.lib_office.add_one_office_opt_full(
                account_name_c, library_name_c, fp_c, fn_c, workspace_fp_c, image_fp_c,
                write_to_filename_c, unique_doc_num_c, user_block_size_c,
                strip_header_c, table_extract_c, smart_chunking_c, max_chunk_size_c,
                encoding_style_c, get_header_text_c, table_grid_c, save_images_c,
                logger_level_c, debug_log_file_c, input_debug_mode_c
            )
        except Exception as e:
            logger.error(f"Error calling C Office parser: {e}")
            raise LLMWareException(f"C Parser Error: {e}")

        output_file_path = parser_tmp_folder / write_to_filename

        blocks = process_parser_output(output_file_path)

        # Update file_type
        for b in blocks:
            b.file_type = "office"

        try:
            if output_file_path.exists():
                output_file_path.unlink()
        except OSError as e:
            logger.warning(f"Could not delete temp file {output_file_path}: {e}")

        return blocks
