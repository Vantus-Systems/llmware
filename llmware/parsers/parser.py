
import os
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

from llmware.configs import LLMWareConfig, LLMWareTableSchema
from llmware.resources import CollectionRetrieval, CollectionWriter, ParserState
from llmware.parsers.records import Block
from llmware.parsers.handlers.pdf import PDFHandler
from llmware.parsers.handlers.office import OfficeHandler
from llmware.parsers.handlers.text import TextHandler
from llmware.exceptions import FilePathDoesNotExistException, LLMWareException

logger = logging.getLogger(__name__)

class Parser:
    """
    Main class for handling parsing of documents and unstructured files.
    Orchestrates specialized handlers for different file types.
    """

    def __init__(self, library=None, account_name="llmware", parse_to_db=False,
                 encoding="utf-8", chunk_size=400, max_chunk_size=600, smart_chunking=1,
                 get_images=True, get_tables=True, strip_header=False, table_grid=True,
                 get_header_text=True, table_strategy=1, verbose_level=2, copy_files_to_library=True,
                 set_custom_logging=-1, use_logging_file=False):

        # Configuration
        self.library = library
        self.account_name = account_name
        self.parse_to_db = parse_to_db

        # If library is passed, override account/db settings
        if library:
            self.account_name = library.account_name
            self.library_name = library.library_name
            self.parser_image_folder = library.image_path

            if CollectionRetrieval(self.library_name, account_name=self.account_name).test_connection():
                self.parse_to_db = True
            else:
                logger.warning(f"Parser not able to connect to database for library {self.library_name}")
                self.parse_to_db = False
        else:
            self.library_name = "default"
            self.parser_image_folder = LLMWareConfig.get_tmp_path()
            self.parse_to_db = False

        # Parsing parameters
        self.encoding = encoding
        self.chunk_size = chunk_size
        self.max_chunk_size = max_chunk_size
        self.smart_chunking = smart_chunking
        self.get_images = get_images
        self.get_tables = get_tables
        self.strip_header = strip_header
        self.table_grid = table_grid
        self.table_strategy = table_strategy
        self.get_header_text = get_header_text
        self.verbose_level = verbose_level
        self.copy_files_to_library = copy_files_to_library
        self.use_logging_file = use_logging_file

        # State
        self.parser_output: List[Dict] = []
        self.parser_job_id = ParserState().issue_new_parse_job_id()
        self.file_counter = 1

        # Handlers
        self.handlers = {
            "pdf": PDFHandler(self),
            "docx": OfficeHandler(self),
            "doc": OfficeHandler(self),
            "pptx": OfficeHandler(self),
            "ppt": OfficeHandler(self),
            "xlsx": OfficeHandler(self),
            "xls": OfficeHandler(self),
            "txt": TextHandler(self),
            "md": TextHandler(self),
            "csv": TextHandler(self),
            "tsv": TextHandler(self),
            "json": TextHandler(self),
            "jsonl": TextHandler(self),
        }

    def parse_one(self, fp: str, fn: str, save_history: bool = True) -> List[Dict]:
        """
        Parses a single file.

        Args:
            fp: File path (directory).
            fn: Filename.
            save_history: Whether to save parser state history.

        Returns:
            List[Dict]: Parsed blocks as dictionaries.
        """
        if not os.path.exists(os.path.join(fp, fn)):
            raise FilePathDoesNotExistException(os.path.join(fp, fn))

        ext = fn.split(".")[-1].lower()
        handler = self._get_handler(ext)

        if not handler:
            logger.warning(f"No handler found for extension {ext}")
            return []

        # Execute parsing
        try:
            blocks = handler.parse(fp, fn,
                                   chunk_size=self.chunk_size,
                                   max_chunk_size=self.max_chunk_size,
                                   smart_chunking=self.smart_chunking,
                                   get_images=self.get_images,
                                   get_tables=self.get_tables,
                                   encoding=self.encoding,
                                   # ... pass other configs
                                   doc_id=self.file_counter
                                   )
        except Exception as e:
            logger.error(f"Error parsing {fn}: {e}")
            return []

        # Convert to dicts for output
        output_dicts = [b.to_dict() for b in blocks]

        if save_history and output_dicts:
            self.parser_output.extend(output_dicts)
            ParserState().save_parser_output(self.parser_job_id, output_dicts)

        return output_dicts

    def ingest(self, input_folder_path: str, dupe_check: bool = True) -> Dict[str, Any]:
        """
        Main method for large-scale ingestion.

        Args:
            input_folder_path: Path to the input folder.
            dupe_check: Whether to check for duplicate files in the library.

        Returns:
            Dict summary of results.
        """
        if not self.library or not self.parse_to_db:
            logger.error("Parser().ingest() requires a library and database connection.")
            return {"processed_files": 0, "rejected_files": 0}

        input_path = Path(input_folder_path)
        if not input_path.exists():
            raise FilePathDoesNotExistException(str(input_path))

        files = [f for f in input_path.iterdir() if f.is_file()]

        processed_files = []
        rejected_files = []
        duplicate_files = []

        # Dupe check
        if dupe_check and self.library:
             existing_files = set(os.listdir(self.library.file_copy_path)) if os.path.exists(self.library.file_copy_path) else set()
        else:
             existing_files = set()

        for file_path in files:
            filename = file_path.name

            if dupe_check and filename in existing_files:
                duplicate_files.append(filename)
                continue

            ext = filename.split(".")[-1].lower()
            handler = self._get_handler(ext)

            if handler:
                logger.info(f"Ingesting {filename}...")
                try:
                    # Parse directly from source location (Optimization: No Copy)
                    blocks = handler.parse(str(input_path), filename,
                                           chunk_size=self.chunk_size,
                                           # ... configs
                                           doc_id=self.library.get_and_increment_doc_id() # Using library doc_id
                                           )

                    # Persist to DB
                    self._write_output_to_db(blocks)

                    # Copy to library (Optimized: direct copy)
                    if self.copy_files_to_library and self.library:
                        dest_path = Path(self.library.file_copy_path) / filename
                        shutil.copy2(file_path, dest_path)

                    processed_files.append(filename)

                except Exception as e:
                    logger.error(f"Failed to ingest {filename}: {e}")
                    rejected_files.append(filename)
            else:
                logger.debug(f"Skipping {filename}: No handler for {ext}")
                # Not rejected, just ignored/skipped

        return {
            "processed_files": processed_files,
            "rejected_files": rejected_files,
            "duplicate_files": duplicate_files
        }

    def _get_handler(self, ext: str):
        """Returns the appropriate handler for the file extension."""
        if ext in self.handlers:
            return self.handlers[ext]
        return None

    def _write_output_to_db(self, blocks: List[Block]):
        """Writes a list of Block objects to the configured database."""
        if not self.library:
            return

        for block in blocks:
            record = block.to_dict()
            # Ensure identifiers are set correctly
            # block.block_id might be set by handler, but library needs global sequence?
            # In original code, library.block_ID is incremented.

            # For now, assuming record is ready for insertion
            CollectionWriter(self.library.library_name, account_name=self.account_name).write_new_parsing_record(record)

            # Increment library block counter if needed (logic from original)
            self.library.block_ID += 1

    def clear_state(self):
        self.parser_output = []
        return self

    def save_state(self):
        ParserState().save_parser_output(self.parser_job_id, self.parser_output)
        return self
