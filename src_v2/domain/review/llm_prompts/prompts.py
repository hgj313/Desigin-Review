"""LLM prompt templates for PRD semantic analysis.

Per D-01: LLM semantic inference for vague language detection
Per D-02: Full Finding output with CRITICAL/HIGH/MEDIUM severity classification
"""

from __future__ import annotations

__all__ = [
    "VAGUE_LANGUAGE_DETECTION_PROMPT",
    "SEMANTIC_COMPLETENESS_PROMPT",
    "CROSS_REFERENCE_VALIDATION_PROMPT",
]

# =============================================================================
# VAGUE_LANGUAGE_DETECTION_PROMPT
# =============================================================================
# Analyzes PRD for vague/ambiguous language patterns requiring LLM inference
# Severity classification per D-02:
#   CRITICAL: Requirement is unmeasurable or completely undefined
#   HIGH: Key acceptance criteria missing or vague
#   MEDIUM: Minor ambiguity that could be clarified

VAGUE_LANGUAGE_DETECTION_PROMPT = """You are an expert design document reviewer analyzing a Product Requirements Document (PRD) for vague or ambiguous language.

## 您的任务 | Your Task
Identify vague language patterns that make requirements difficult to verify or implement.

## 严重程度分类 | Severity Classification
- **CRITICAL (严重)**: Requirement is unmeasurable or completely undefined
  - Examples: "perform fast", "user-friendly", "robust", "as needed" in acceptance criteria
- **HIGH (高)**: Key acceptance criteria missing or vague
  - Examples: "as appropriate", "etc.", "and so on", unquantified terms
- **MEDIUM (中)**: Minor ambiguity that could be clarified
  - Examples: "TBD" in non-planning sections, "approximately" without range

## 模糊语言模式 | Vague Language Patterns to Detect
1. Unquantified terms: "fast", "robust", "efficient", "user-friendly", "seamless"
2. Placeholders: "TBD", "to be determined", "pending", "as needed"
3. Vague quantifiers: "as appropriate", "as necessary", "etc.", "and so on"
4. Missing specifics: no numbers, no dates, no clear success criteria
5. Conditional vagueness: "if needed", "when appropriate", "may vary"

## 输出格式 | Output Format
Return a JSON array of findings:
```json
[
  {{
    "location": "Section name or line reference",
    "severity": "CRITICAL|HIGH|MEDIUM",
    "description": "What makes this language vague",
    "suggestion": "How to make this more specific",
    "evidence": "The actual text that is vague"
  }}
]
```

## 文档内容 | Document Content
Analyze the following PRD content:

{content}

## 要求 | Requirements
1. Return ONLY valid JSON array (no markdown code blocks)
2. Each finding must have all 5 fields
3. Use Chinese/English bilingual descriptions where helpful
4. Focus on actionable findings that can improve the PRD quality
"""

# =============================================================================
# SEMANTIC_COMPLETENESS_PROMPT
# =============================================================================
# Checks PRD structure completeness per PRD-01 requirements
# Validates presence of required sections and their semantic elements

SEMANTIC_COMPLETENESS_PROMPT = """You are an expert PRD reviewer checking document completeness and semantic coverage.

## 您的任务 | Your Task
Analyze whether the PRD covers all required semantic elements for a complete product specification.

## 必需部分 | Required Sections (per PRD-01)
1. **Overview (概述)**: Purpose, scope, target users
2. **User Stories (用户故事)**: Who, what, why for each user type
3. **Functional Requirements (功能需求)**: Specific behaviors and features
4. **Non-Functional Requirements (非功能需求)**: Performance, security, usability
5. **Acceptance Criteria (验收标准)**: Measurable conditions for success
6. **Technical Constraints (技术约束)**: Technology stack, integrations, limitations

## 严重程度 | Severity Classification
- **CRITICAL**: Essential section completely missing (Overview, User Stories, or Acceptance Criteria)
- **HIGH**: Key section present but semantically incomplete
- **MEDIUM**: Minor section missing or generic content

## 语义完整性检查 | Semantic Completeness Checks
- User Stories: Do they have clear actor, action, and benefit?
- Acceptance Criteria: Are they measurable (SMART: Specific, Measurable, Achievable, Relevant, Time-bound)?
- Functional Requirements: Do they trace to user stories?
- Non-Functional Requirements: Are metrics specified (response time, throughput, etc.)?

## 输出格式 | Output Format
Return a JSON object:
```json
{{
  "completeness_score": 0-100,
  "sections": [
    {{
      "name": "Section name",
      "present": true|false,
      "completeness": "complete|partial|missing",
      "severity": "CRITICAL|HIGH|MEDIUM|NONE",
      "issues": ["List of issues if any"],
      "suggestions": ["How to improve"]
    }}
  ],
  "findings": [
    {{
      "location": "Section name",
      "severity": "CRITICAL|HIGH|MEDIUM",
      "description": "What's incomplete or missing",
      "suggestion": "How to fix"
    }}
  ]
}}
```

## 文档内容 | Document Content
Analyze the following PRD:

{content}
"""

# =============================================================================
# CROSS_REFERENCE_VALIDATION_PROMPT
# =============================================================================
# Validates user story to design specification links per D-03, D-04
# Uses semantic similarity threshold >= 0.7 for association

CROSS_REFERENCE_VALIDATION_PROMPT = """You are an expert at validating cross-references in design documents.

## 您的任务 | Your Task
Validate that user stories in the PRD have corresponding design specifications, and identify which user stories lack proper design backing.

## 背景 | Background
- D-03: Semantic embedding matching for cross-reference validation
- D-04: Fixed threshold 0.7 for similarity matching
- D-05: Standard Not Found pattern when below threshold

## 关联性判断 | Association Criteria
A user story and design spec are associated when:
1. They describe the same user action or workflow
2. The design spec provides visual/component details for the story
3. Semantic similarity >= 0.7 (or "Standard Not Found" if below)

## 阈值处理 | Threshold Handling
- **Associated (>= 0.7)**: User story has design spec backing
- **Standard Not Found (< 0.7)**: No adequate design spec found; needs attention

## 输出格式 | Output Format
Return a JSON array of user stories with their validation status:
```json
[
  {{
    "user_story_id": "US-001",
    "user_story_text": "The user story text",
    "has_design_spec": true|false,
    "similarity_score": 0.0-1.0,
    "related_specs": [
      {{
        "spec_id": "SPEC-001",
        "spec_title": "Design spec title",
        "similarity": 0.0-1.0
      }}
    ],
    "status": "associated|standard_not_found",
    "suggestion": "If standard_not_found, what design spec is needed"
  }}
]
```

## 用户故事 | User Stories
{user_stories}

## 设计规范 | Design Specifications
{design_specs}
"""
