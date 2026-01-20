
import os
import platform
import logging
from ctypes import *
from enum import IntEnum
from pathlib import Path
from typing import Optional, Any

from llmware.configs import LLMWareConfig
from llmware.exceptions import ModuleNotFoundException, LLMWareException

logger = logging.getLogger(__name__)

class DebugMode(IntEnum):
    """Debug mode flags for C parsers."""
    OFF = 0
    FILE_LOGGING = 60
    # Add other modes if known, but 0 and 60 seem to be the main ones used.

class ImageSaveMode(IntEnum):
    """Image save mode flags."""
    OFF = 0
    ON = 1

class TableExtractMode(IntEnum):
    """Table extraction strategies."""
    OFF = 0
    STRATEGY_1 = 1
    STRATEGY_2 = 2

class EncodingStyle(IntEnum):
    """Encoding styles."""
    ASCII = 0
    LATIN_1 = 1
    UTF_8 = 2

class ParserBindings:
    """Singleton wrapper for C-library bindings."""

    _instance: Optional['ParserBindings'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ParserBindings, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.lib_pdf = None
        self.lib_office = None
        self._load_libraries()
        self._initialized = True

    def _get_library_path(self, lib_name: str) -> Path:
        """Determines the correct library path based on platform."""

        system = platform.system().lower()
        machine = platform.machine().lower()

        # Normalize machine names
        if system == 'linux':
            try:
                machine = os.uname().machine.lower()
            except:
                pass

        if machine in ['amd64', 'x86_64']:
            machine = 'x86_64'
        elif machine in ['arm64', 'aarch64']:
            machine = 'arm64'

        # Adjust for folder naming conventions in llmware/lib
        # Windows: windows/x86_64 or windows/arm64
        # Linux: linux/x86_64
        # Mac: darwin/arm64 or darwin/x86_64 (deprecated)

        if system == 'windows':
            file_ext = '.dll'
        else:
            file_ext = '.so'

        # Map system/machine to folder structure
        folder_system = system
        folder_machine = machine

        # Handling specific overrides from util.py logic normalization
        if system == 'darwin':
            if machine not in ['arm64', 'x86_64']:
                folder_machine = 'arm64'

        if system == 'linux':
             if machine not in ['arm64', 'x86_64']:
                 folder_machine = 'x86_64'

        lib_path = Path(LLMWareConfig.get_config("shared_lib_path")) / folder_system / folder_machine / "llmware" / (lib_name + file_ext)
        return lib_path

    def _load_libraries(self):
        """Loads the shared libraries."""

        # PDF Parser
        pdf_lib_path = self._get_library_path("libpdf_llmware")
        try:
            self.lib_pdf = cdll.LoadLibrary(str(pdf_lib_path))
            self._setup_pdf_bindings()
            logger.info(f"Loaded PDF Parser library from {pdf_lib_path}")
        except OSError as e:
            logger.warning(f"Could not load PDF Parser library from {pdf_lib_path}: {e}")
            self.lib_pdf = None

        # Office Parser
        office_lib_path = self._get_library_path("liboffice_llmware")
        try:
            self.lib_office = cdll.LoadLibrary(str(office_lib_path))
            self._setup_office_bindings()
            logger.info(f"Loaded Office Parser library from {office_lib_path}")
        except OSError as e:
            logger.warning(f"Could not load Office Parser library from {office_lib_path}: {e}")
            self.lib_office = None

    def _setup_pdf_bindings(self):
        """Sets up ctypes bindings for PDF parser functions."""
        if not self.lib_pdf:
            return

        # add_pdf_main_llmware_config_new
        self.lib_pdf.add_pdf_main_llmware_config_new.argtypes = (
            c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p,
            c_char_p, c_int, c_int, c_int, c_char_p, c_int, c_int, c_int, c_int, c_char_p,
            c_int, c_int, c_int, c_int, c_int, c_int, c_int,
            c_int, c_char_p
        )
        self.lib_pdf.add_pdf_main_llmware_config_new.restype = c_int

        # add_one_pdf_opts
        self.lib_pdf.add_one_pdf_opts.argtypes = (
            c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_char_p, c_int,
            c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int,
            c_char_p, c_int
        )
        self.lib_pdf.add_one_pdf_opts.restype = c_int

    def _setup_office_bindings(self):
        """Sets up ctypes bindings for Office parser functions."""
        if not self.lib_office:
            return

        # add_files_main_llmware_opt_full
        self.lib_office.add_files_main_llmware_opt_full.argtypes = (
            c_char_p, c_char_p, c_char_p, c_char_p, c_char_p,
            c_char_p, c_char_p, c_char_p, c_char_p, c_char_p,
            c_int, c_int, c_char_p, c_int, c_int, c_int, c_int,
            c_char_p, c_int, c_int, c_int, c_int, c_int, c_int,
            c_int, c_int, c_int, c_char_p
        )
        self.lib_office.add_files_main_llmware_opt_full.restype = c_int

        # add_one_office_opt_full
        self.lib_office.add_one_office_opt_full.argtypes = (
            c_char_p, c_char_p, c_char_p, c_char_p, c_char_p,
            c_char_p, c_char_p, c_int, c_int, c_int, c_int, c_int,
            c_int, c_int, c_int, c_int, c_int, c_int, c_char_p, c_int
        )
        self.lib_office.add_one_office_opt_full.restype = c_int
