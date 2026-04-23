"""PRD Domain - PRD document review bounded context.

Entities:
- PRDDocument: Main PRD document aggregate
- Section: A section within the PRD

Services:
- PRDStructureValidator: Validates PRD structure
- PRDTerminologyChecker: Checks terminology consistency
"""

from .entities import PRDDocument, Section
from .services import PRDStructureValidator, PRDTerminologyChecker

__all__ = [
    "PRDDocument",
    "Section",
    "PRDStructureValidator",
    "PRDTerminologyChecker",
]
