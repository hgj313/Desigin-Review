"""PRD Domain Services - Structure validation and terminology checking.

Services:
- PRDStructureValidator: Validates PRD has required sections
- PRDTerminologyChecker: Checks terminology against design glossary

References:
- ARCHITECTURE.md: PRD Context Services section
- FEATURES.md: PRD validation tools
"""

from typing import Optional

from src.domains.prd.entities import PRDDocument, Section
from src.domains.shared import Finding, SeverityLevel, ReviewDimension


# Required sections per design standards
REQUIRED_SECTIONS = [
    "overview",
    "user stories",
    "acceptance criteria",
    "requirements",
]

# Section title variations (for fuzzy matching)
SECTION_VARIATIONS = {
    "overview": ["overview", "introduction", "背景", "概述"],
    "user stories": ["user stories", "user story", "用户故事", "用户需求"],
    "acceptance criteria": ["acceptance criteria", "验收标准", "ac"],
    "requirements": ["requirements", "功能需求", "非功能需求"],
}


class PRDStructureValidator:
    """Validates PRD structure against design standards.

    Checks for:
    - Required sections presence
    - Heading hierarchy (H1 > H2 > H3)
    - No empty sections
    - Logical document flow
    """

    def __init__(self, required_sections: Optional[list[str]] = None):
        """Initialize validator.

        Args:
            required_sections: List of required section names.
                               Defaults to REQUIRED_SECTIONS.
        """
        self.required_sections = required_sections or REQUIRED_SECTIONS

    def validate(self, doc: PRDDocument, standards: Optional[list[str]] = None) -> list[Finding]:
        """Validate PRD document structure.

        Args:
            doc: PRD document to validate
            standards: Optional design standards to check against

        Returns:
            List of findings (empty if no issues)
        """
        findings = []

        # Check required sections
        findings.extend(self._check_required_sections(doc))

        # Check heading hierarchy
        findings.extend(self._check_heading_hierarchy(doc))

        # Check for empty sections
        findings.extend(self._check_empty_sections(doc))

        # Check for placeholder content
        findings.extend(self._check_placeholders(doc))

        return findings

    def _check_required_sections(self, doc: PRDDocument) -> list[Finding]:
        """Check if all required sections are present."""
        findings = []
        doc_sections_lower = {s.title.lower() for s in doc.sections}

        for required in self.required_sections:
            # Check if any variation matches
            variations = SECTION_VARIATIONS.get(required, [required])
            found = any(var in doc_sections_lower for var in variations)

            if not found:
                findings.append(Finding(
                    source_context="prd",
                    dimension=ReviewDimension.STRUCTURE,
                    severity=SeverityLevel.HIGH,
                    rule_id="prd-struct-001",
                    description=f"Missing required section: {required}",
                    location="Document structure",
                    suggestion=f"Add a '{required}' section to the PRD",
                    evidence=f"Required sections: {', '.join(self.required_sections)}",
                ))

        return findings

    def _check_heading_hierarchy(self, doc: PRDDocument) -> list[Finding]:
        """Check heading level hierarchy."""
        findings = []

        for i, section in enumerate(doc.sections):
            if section.level == 1:
                continue  # H1 is fine as top level

            # Check if there's a parent heading
            parent_found = False
            for j in range(i - 1, -1, -1):
                if doc.sections[j].level < section.level:
                    parent_found = True
                    break

            if not parent_found and section.level > 1:
                findings.append(Finding(
                    source_context="prd",
                    dimension=ReviewDimension.STRUCTURE,
                    severity=SeverityLevel.MEDIUM,
                    rule_id="prd-struct-002",
                    description=f"Section '{section.title}' has level H{section.level} but no parent heading",
                    location=f"Section: {section.title}",
                    suggestion="Ensure heading levels increase gradually (H1 > H2 > H3)",
                ))

        return findings

    def _check_empty_sections(self, doc: PRDDocument) -> list[Finding]:
        """Check for empty or near-empty sections."""
        findings = []

        for section in doc.sections:
            if section.is_heading_only():
                findings.append(Finding(
                    source_context="prd",
                    dimension=ReviewDimension.STRUCTURE,
                    severity=SeverityLevel.MEDIUM,
                    rule_id="prd-struct-003",
                    description=f"Section '{section.title}' has no content",
                    location=f"Section: {section.title}",
                    suggestion="Add content to this section or remove the heading",
                ))

        return findings

    def _check_placeholders(self, doc: PRDDocument) -> list[Finding]:
        """Check for placeholder text in content."""
        findings = []
        placeholders = ["TODO", "TBD", "xxx", "...", "[TODO]", "[待定]"]

        for section in doc.sections:
            for placeholder in placeholders:
                if placeholder in section.content:
                    findings.append(Finding(
                        source_context="prd",
                        dimension=ReviewDimension.STRUCTURE,
                        severity=SeverityLevel.MEDIUM,
                        rule_id="prd-struct-004",
                        description=f"Found placeholder text: '{placeholder}'",
                        location=f"Section: {section.title}",
                        suggestion="Replace placeholder with actual content",
                    ))

        return findings


class PRDTerminologyChecker:
    """Checks PRD terminology against design standards glossary.

    Validates:
    - Consistent use of design terms
    - No mixed Chinese/English inconsistencies
    - Proper naming conventions
    """

    def __init__(self, glossary: Optional[dict[str, str]] = None):
        """Initialize checker.

        Args:
            glossary: Dict of approved terms {term: definition}
                     Defaults to built-in design glossary.
        """
        self.glossary = glossary or self._default_glossary()

    def _default_glossary(self) -> dict[str, str]:
        """Get default design terminology glossary."""
        return {
            # Design system terms
            "按钮": "Button",
            "输入框": "Input",
            "卡片": "Card",
            "导航": "Navigation",
            "菜单": "Menu",
            "表单": "Form",
            "弹窗": "Modal/Dialog",
            "侧边栏": "Sidebar",
            "工具栏": "Toolbar",
            "状态": "Status/State",
            "标签": "Tag/Label",
            "图标": "Icon",
            "头像": "Avatar",
            "头像框": "Avatar",
            "开关": "Switch/Toggle",
            "复选框": "Checkbox",
            "单选框": "Radio",
            "下拉框": "Dropdown/Select",
            "滑块": "Slider",
            "进度条": "Progress Bar",
            "骨架屏": "Skeleton",
            "空状态": "Empty State",
            "错误状态": "Error State",
            "加载状态": "Loading State",
            # UX terms
            "用户故事": "User Story",
            "验收标准": "Acceptance Criteria",
            "功能需求": "Functional Requirement",
            "非功能需求": "Non-Functional Requirement",
            "用例": "Use Case",
            "流程": "Flow/Process",
            "交互": "Interaction",
            "反馈": "Feedback",
            "提示": "Hint/Tip",
            "错误提示": "Error Message",
            "成功提示": "Success Message",
            # Spacing terms
            "间距": "Spacing",
            "边距": "Margin",
            "内边距": "Padding",
            "组件间距": "Component Spacing",
            "页面边距": "Page Margin",
        }

    def check(self, doc: PRDDocument, standards: Optional[list[str]] = None) -> list[Finding]:
        """Check PRD terminology consistency.

        Args:
            doc: PRD document to check
            standards: Optional terminology standards

        Returns:
            List of findings (empty if no issues)
        """
        findings = []

        # Check each section content
        for section in doc.sections:
            findings.extend(self._check_section_terminology(section))

        # Check for mixed language issues
        findings.extend(self._check_mixed_language(doc))

        return findings

    def _check_section_terminology(self, section: Section) -> list[Finding]:
        """Check terminology in a section."""
        findings = []
        content = section.content

        # Look for unapproved Chinese terms that have English equivalents
        for cn_term, en_term in self.glossary.items():
            # Check if Chinese term appears without its English equivalent nearby
            if cn_term in content:
                # Simple heuristic: if Chinese term exists, suggest English
                findings.append(Finding(
                    source_context="prd",
                    dimension=ReviewDimension.TERMINOLOGY,
                    severity=SeverityLevel.LOW,
                    rule_id="prd-term-001",
                    description=f"Use consistent terminology: '{cn_term}' should be '{en_term}'",
                    location=f"Section: {section.title}",
                    suggestion=f"Use '{en_term}' (English) for consistency with design standards",
                    evidence=f"Found: {cn_term}",
                ))

        return findings

    def _check_mixed_language(self, doc: PRDDocument) -> list[Finding]:
        """Check for mixed Chinese/English in same section."""
        findings = []

        # This is a simplified check - full implementation would use
        # more sophisticated language detection
        for section in doc.sections:
            content = section.content
            # Very rough heuristic
            if any('一' <= c <= '鿿' for c in content):  # Has Chinese
                # Check for excessive English mixed in
                english_words = sum(1 for c in content if c.isascii() and c.isalpha())
                chinese_chars = sum(1 for c in content if '一' <= c <= '鿿')
                if english_words > 50 and chinese_chars > 50:
                    findings.append(Finding(
                        source_context="prd",
                        dimension=ReviewDimension.TERMINOLOGY,
                        severity=SeverityLevel.LOW,
                        rule_id="prd-term-002",
                        description="Section has mixed Chinese and English content",
                        location=f"Section: {section.title}",
                        suggestion="Consider using primarily one language for consistency",
                    ))
                    break  # Only flag once per document

        return findings
