# ROADMAP.md - v2.0 Production Readiness | 项目路线图

**项目：** Design Doc Review Expert Agent
**里程碑：** v2.0 Production Readiness
**创建日期：** 2026/04/22
**粒度：** 粗粒度（4 phases）
**并行化：** 已启用

---

## 概述 | Overview

v2.0 在 v1.1 基础上**完全重构**，采用真正的 DDD 架构。

**核心价值：** 从"能用"到"好用"——更准确的语义分析、更全面的原型检查、更直观的趋势跟踪。

**关键原则：**
- 新代码在 `src_v2/` 目录，与 `src/`（v1.1 参考代码）完全分离
- 领域层 (Domain) 是核心，不是边缘化
- Agent 是编排者，业务逻辑在领域服务中

**架构划分：**
```
src/                    # v1.1 参考存档（只读）
src_v2/                 # v2.0 全新 DDD 实现
├── domain/             # 领域层（核心）
│   ├── ingestion/      # 摄取上下文
│   ├── review/         # 审查上下文（核心）
│   ├── reporting/       # 报告上下文
│   └── shared/         # 共享内核
├── infrastructure/     # 基础设施层
├── application/         # 应用层
└── agents/             # Agent 层
```

---

## Phase 7-10

- [ ] **Phase 7: DDD 骨架** - 建立领域层骨架、接口定义
- [x] **Phase 8: Ingestion + Retrieval** - 实现摄取和检索上下文 (completed 2026-04-23)
- [ ] **Phase 9: Review Context** - 实现审查上下文（核心）
  - [ ] 09-01-PLAN.md — Foundation: CIEDE2000 + LLM prompts
  - [ ] 09-02-PLAN.md — PRD Reviewer Service
  - [ ] 09-03-PLAN.md — Prototype Reviewer Service
- [ ] **Phase 10: Reporting + Agent** - 实现报告上下文和 Agent 编排

---

## Phase 详情

### Phase 7: DDD 骨架

**目标：** 建立领域层骨架，定义实体、服务、仓库接口

**依赖：** 无（全新开始）

**成功标准**:
1. `src_v2/domain/` 目录结构建立
2. 三个限界上下文清晰划分
3. 实体定义完成（Document, Chunk, Standard, Finding, Report）
4. 服务接口定义完成
5. 仓库接口定义完成（IDocumentRepository, IStandardRepository, IReportRepository）
6. 共享内核定义完成（Finding, Severity, ReviewContext）

### Phase 8: Ingestion + Retrieval Context

**目标：** 实现摄取和检索上下文

**依赖：** Phase 7

**成功标准**:
1. 自适应分块：根据内容类型选择最优分块策略
2. 知识图谱：建立标准间的关联关系
3. 混合检索：向量搜索 + 图谱遍历结合
4. 检索精度提升 20%

### Phase 9: Review Context

**目标：** 实现审查上下文（核心领域）

**依赖：** Phase 8

**成功标准**:
1. 模糊语言检测：识别 "as needed"、"etc."、"TBD" 等
2. 交叉引用验证：用户故事与设计规范关联
3. 多图输入：支持多个原型图同时分析
4. 一致性检测：颜色/字体/间距跨屏幕一致性

**Plans:**
- 09-01-PLAN.md — Foundation: colormath + CIEDE2000 calculator + LLM prompts
- 09-02-PLAN.md — PRD Reviewer Service: vague language detection + cross-reference validation
- 09-03-PLAN.md — Prototype Reviewer Service: color/typography/spacing consistency

### Phase 10: Reporting + Agent Orchestration

**目标：** 实现报告上下文和 Agent 编排

**依赖：** Phase 9

**成功标准**:
1. 历史记录：存储历次审查结果
2. 趋势指标：合规分数变化、问题类型分布
3. LangGraph Agent 编排完整工作流
4. 端到端审查流程可运行

---

## 覆盖率验证

### 需求映射

| Phase | v2.0 需求 |
|-------|----------|
| Phase 7: DDD 骨架 | DDD-01, DDD-02, DDD-03 |
| Phase 8: Ingestion + Retrieval | RAG-01, RAG-02 |
| Phase 9: Review Context | PRD-01, PRD-02, PRD-05, PROTO-01, PROTO-02 |
| Phase 10: Reporting + Agent | RPT-01, RPT-02, AGT-01 |

### 覆盖率总结

| 指标 | 值 |
|------|-----|
| v2.0 需求总数 | 10 |
| 映射到 phases | 10 |
| 未映射 | 0 |

---

## Phase 依赖关系

```
Phase 7 (DDD 骨架)
         │
         ▼
Phase 8 (Ingestion + Retrieval)
         │
         ▼
Phase 9 (Review Context)
         │
         ▼
Phase 10 (Reporting + Agent)
```

---

## v1.1 vs v2.0 对比

| 方面 | v1.1 | v2.0 |
|------|------|------|
| 代码位置 | `src/` | `src_v2/` |
| 架构 | 工具编排为主 | DDD 领域为核心 |
| 分块 | 固定大小 | 自适应类型 |
| 检索 | 纯向量 | 混合向量+图谱 |
| PRD 分析 | 规则匹配 | LLM 语义 |
| 原型分析 | 单图 | 多图一致性 |
| 报告 | 单次 | 趋势跟踪 |
| 状态管理 | 混合 | TypedDict 清晰分离 |

---

*最后更新：2026/04/23 - Phase 9 plans added*
