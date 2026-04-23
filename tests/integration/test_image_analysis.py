#!/usr/bin/env python3
"""Test image understanding + vector storage flow."""

import sys
sys.path.insert(0, ".")

from src_v2.domain.ingestion.entities import Document, DocumentContentType
from src_v2.infrastructure.chunking.adaptive_chunker import AdaptiveChunkingService
from src_v2.infrastructure.embeddings.bge_m3_embedding import BgeM3EmbeddingService
from src_v2.infrastructure.vectorstore.chroma_store import ChromaStore
from src_v2.infrastructure.ingestion.chunk_repository_impl import ChunkRepositoryImpl

# Image analysis result from MiniMax vision model
image_analysis = """
这是一份关于"吉盛生态 (GSE)"管理系统的原型图详细分析：

### 1. 界面类型
这是一份典型的B端（企业级）管理系统界面，属于 ERP 或 PMIS 的一部分。
功能定位：核心功能是"项目里程碑"监控仪表盘，用于跟踪多个项目的进度、状态及报表填报情况。

### 2. 主要 UI 元素和组件
- 顶部导航栏 (Top Navigation)：包含系统 Logo、一级功能模块、个人中心及系统设置工具栏。
- 侧边导航栏 (Sidebar)：垂直排列的二级/三级菜单，带有关联图标和展开/收起功能。
- 页签组件 (Tabs)：位于内容区顶部，支持多任务并行处理。
- 筛选/搜索栏 (Filter Bar)：包含下拉选择框（区域、项目、项目经理）和日期范围选择器。
- 状态图例 (Legend)：使用图标+颜色+文字+数字的方式，直观展示各类进度的统计摘要。
- 数据表格 (Data Table)：界面核心，包含复选框、状态标签（Tags）、进度百分比、状态图标以及操作链接。
- 气泡卡片/工具提示 (Tooltip)：鼠标悬停时显示的浮窗。

### 3. 布局结构
采用标准的"T型"或"L型"布局：
- 顶部 (Header)：全局导航和控制
- 左侧 (Sidebar)：功能层级导航
- 主体 (Main Content)：包含页签、过滤筛选、KPI汇总、数据列表

### 4. 颜色使用特点
- 品牌色：深青色/蓝绿色，体现生态、稳重的品牌调性
- 语义化配色：
  * 绿色 (Success)：代表"正常完成"或"竣工"
  * 橙色/黄色 (Warning)：代表"延期完成"或"延期进行中"
  * 红色 (Error/Danger)：代表"延期未完成"或逾期预警
  * 蓝色 (Processing)：代表"在建"或"进行中"
- 中性色：背景使用浅灰和白色，文字采用深灰和黑色

### 5. 可访问性分析
优势：
- 冗余编码：状态表达不仅依赖颜色，还结合了不同的图标形状
- 清晰的层级：字体加粗与颜色对比区分了表头与表项

潜在问题：
- 文本对比度：某些彩色标签对比度可能较低
- 信息密度过大：界面拥挤，字体较小
- 悬停依赖：关键信息隐藏在 Tooltip 中
- 交互目标较小：右侧"项目详情"链接文字细小
"""

def test_image_analysis_storage():
    """Test storing image analysis in vector database."""
    print("=" * 60)
    print("Testing Image Analysis Storage")
    print("=" * 60)

    chunking = AdaptiveChunkingService()
    embedding = BgeM3EmbeddingService()
    vector_store = ChromaStore(collection_name="image_analysis_test")
    repo = ChunkRepositoryImpl(vector_store, embedding)

    doc = Document(
        id="prototype-001",
        content=image_analysis,
        content_type=DocumentContentType.GENERAL,
        metadata={
            "source": "Prd-test/工程看板原型图.png",
            "type": "image_analysis",
            "interface_type": "ERP/PMIS Dashboard",
        },
    )

    print("[*] Chunking image analysis...")
    chunks = chunking.chunk_document(doc)
    print(f"    Created {len(chunks)} chunks")

    print("[*] Storing chunks in vector database...")
    for chunk in chunks:
        repo.store_chunk(chunk)
    print(f"    Stored {len(chunks)} chunks")

    # Test retrieval against design standards
    print("\n[*] Testing retrieval with design queries...")

    queries = [
        ("颜色对比度要求", "查询颜色对比度相关的设计标准"),
        ("移动端间距要求", "查询移动端间距标准"),
        ("可访问性设计", "查询可访问性设计规范"),
        ("表格布局设计", "查询表格布局设计规范"),
    ]

    for query, description in queries:
        emb = embedding.embed_query(query)
        results = repo.find_similar(emb, k=2)
        print(f"\n    Query: '{query}' ({description})")
        for i, (doc, score) in enumerate(results):
            print(f"    [{i+1}] Score: {score:.4f} | {doc.page_content[:100]}...")

    vector_store.delete_collection()
    print("\n[+] Image analysis storage test completed!")

if __name__ == "__main__":
    test_image_analysis_storage()
    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)