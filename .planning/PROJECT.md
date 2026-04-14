# Design Doc Review Expert Agent
# 设计文档审查专家 Agent

## What This Is | 这是什么

An AI-powered expert agent that reviews product PRD documents and prototype images against company design standards, using a RAG-based vector knowledge库. The agent provides detailed compliance reports highlighting issues and improvement suggestions.

一个 AI 驱动的专家 Agent，通过基于 RAG 的向量知识库审查产品 PRD 文档和原型图是否符合公司设计标准规范。Agent 提供详细的合规报告，列出问题和高改进建议。

## Core Value | 核心价值

**Automate design compliance review at scale.** Replace manual, inconsistent reviews with consistent, scalable AI-powered validation. This is a learning project to master RAG + Agent patterns.

**自动化设计合规审查。** 用一致的、可扩展的 AI 验证替代手动、不一致的审查。这是一个学习项目，用于掌握 RAG + Agent 模式。

## Requirements | 需求

### Active | 活跃需求

- [ ] **RAG Knowledge Base | RAG 知识库**: Ingest 100+ pages of design standards into a searchable vector store | 将 100+ 页设计标准摄入到可检索向量存储
- [ ] **PRD Review | PRD 审查**: Validate PRD structure, terminology, completeness against standards | 根据标准验证 PRD 结构、术语、完整性
- [ ] **Prototype Review | 原型图审查**: Check layout, color, typography, spacing against design specs | 根据设计规范检查布局、颜色、字体、间距
- [ ] **Compliance Report | 合规报告**: Generate detailed report with issues, severity, and improvement suggestions | 生成包含问题、严重程度和改进建议的详细报告
- [ ] **Bilingual Output | 双语输出**: All outputs in Chinese and English | 所有输出均为中英双语

### Out of Scope | 范围外

- Real-time collaboration features | 实时协作功能
- Multi-user workflow management | 多用户工作流管理
- Direct Figma/Axure integration | 直接集成 Figma/Axure
- Automated fixing of issues | 自动修复问题

## Context | 上下文

**Learning Project | 学习项目**: Primary goal is to learn and practice RAG + Agent development patterns, not production deployment. Tech stack decisions should balance learning value with practical applicability.

**学习项目**: 主要目标是学习和实践 RAG + Agent 开发模式，而非生产部署。技术栈决策应平衡学习价值与实际适用性。

**No Live Standards Docs | 无实时标准文档**: Design standards are assumed to exist as documents but actual content will be synthesized for development. Real standards ingestion is a future phase.

**无实时标准文档**: 假设设计标准以文档形式存在，但实际内容将为开发而综合。实时标准摄入是未来阶段。

## Constraints | 约束

- **Tech Stack**: LangChain (RAG/Retrieval) + LangGraph (Workflow Orchestration) — both complementary, not competing | 互补使用，不竞争
- **Vector DB**: Choice needed — options include Chroma (local), Pinecone (cloud), Qdrant | 待选择
- **LLM**: Choice needed — Claude, GPT-4, or local model | 待选择
- **Review Coverage**: Full dimension coverage (structure, terminology, layout, accessibility) | 全维度覆盖
- **Scale**: Designed for 100+ page knowledge base | 为 100+ 页知识库设计

## Key Decisions | 关键决策

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| LangChain + LangGraph hybrid | LangChain for retrieval生态, LangGraph for complex workflow | — Pending |
| Chunking strategy | 100+ pages requires thoughtful splitting | — Pending |
| Vector DB selection | Local vs cloud tradeoffs for learning | — Pending |
| LLM selection | Quality vs cost vs privacy | — Pending |

## Evolution | 演进

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026/04/14 after initialization*
