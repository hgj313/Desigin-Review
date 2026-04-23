"""Checkpoint configuration for LangGraph workflow recovery.

Provides checkpointers for development and production use.

References:
- ARCHITECTURE.md: Checkpointing section
- STACK.md: MemorySaver vs SqliteSaver
"""

from langgraph.checkpoint.memory import MemorySaver
from typing import Optional


def create_memory_checkpointer() -> MemorySaver:
    """Create MemorySaver checkpointer for development.

    Usage:
        checkpointer = create_memory_checkpointer()
        app = workflow.compile(checkpointer=checkpointer)
    """
    return MemorySaver()


def create_sqlite_checkpointer(db_path: str):
    """Create SqliteSaver checkpointer for single-node production.

    Args:
        db_path: Path to SQLite database file

    Usage:
        checkpointer = create_sqlite_checkpointer("./checkpoints.db")
        app = workflow.compile(checkpointer=checkpointer)
    """
    from langgraph.checkpoint.sqlite import SqliteSaver
    return SqliteSaver.from_conn_string(f"sqlite:///{db_path}")


def create_postgres_checkpointer(conn_string: str):
    """Create PostgresSaver checkpointer for multi-node production.

    Args:
        conn_string: PostgreSQL connection string

    Usage:
        checkpointer = create_postgres_checkpointer(
            "postgresql://user:pass@localhost:5432/langgraph"
        )
        app = workflow.compile(checkpointer=checkpointer)
    """
    from langgraph.checkpoint.postgres import PostgresSaver
    return PostgresSaver.from_conn_string(conn_string)


# Default checkpointer for development
default_checkpointer = create_memory_checkpointer()
