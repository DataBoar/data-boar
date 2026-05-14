"""
Factory for different types of scanners
"""

from typing import Dict, Type
from src.scanners.base_scanner import BaseScanner
from src.scanners.db_scanner import DatabaseScanner
from src.scanners.file_scanner import FileScanner


class ScannerFactory:
    scanners: Dict[str, Type[BaseScanner]] = {
        "db": DatabaseScanner,
        "file": FileScanner,
    }

    @staticmethod
    def get_scanner(name: str) -> BaseScanner:
        """Get scanner by name"""
        return ScannerFactory.scanners.get(name)()
