"""
Base Database Adapter Interface for PgSafe.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple

class BaseAdapter(ABC):
    @abstractmethod
    def connect(self):
        """Establishes database connection."""
        pass

    @abstractmethod
    def list_tables(self) -> List[str]:
        """Returns list of user tables in the database."""
        pass

    @abstractmethod
    def describe_table(self, table_name: str) -> List[Dict[str, Any]]:
        """Returns column names, types, and constraints for a table."""
        pass

    @abstractmethod
    def execute_read_only(self, sql: str) -> Tuple[List[str], List[List[Any]]]:
        """Executes a read-only query and returns (columns, rows)."""
        pass
