# Code-RAG Hub 技术选型分析报告

**文档版本**: v1.0  
**分析日期**: 2026-03-19  
**关联文档**: 01-RagHubMCP_20260319.md  

---

## 📋 目录

1. [选型背景与约束](#一选型背景与约束)
2. [语言对比分析](#二语言对比分析)
3. [核心结论](#三核心结论)
4. [模型后端抽象设计](#四模型后端抽象设计)
5. [代码切分插件化设计](#五代码切分插件化设计)
6. [最终技术栈](#六最终技术栈)
7. [待确认事项](#七待确认事项)

---

## 一、选型背景与约束

### 1.1 项目定位

**Code-RAG Hub** - 通用代码 RAG 中枢，作为 IDE 与 AI 模型之间的智能桥梁。

**核心定位**: 
- 做 **HUB**，不做固定模型
- 支持多种模型后端（Ollama、llama.cpp、LM Studio、外部 API）
- 通过 MCP 协议连接多种 IDE

### 1.2 技术约束

| 约束项 | 已确认选择 | 说明 |
|--------|-----------|------|
| 向量数据库 | Chroma | 已安装，MVP 首选 |
| 后端框架 | FastAPI | 已确认 |
| 前端框架 | Vue 3 + shadcn | 初期简化实现 |
| 协议层 | MCP | Model Context Protocol |
| 代码解析 | Tree-sitter/AST | 作为插件，滞后考虑 |

### 1.3 待决策问题

- **后端语言**: Python / TypeScript / Rust / Go？
- **是否需要双语言架构？**
- **模型后端如何抽象？**

---

## 二、语言对比分析

### 2.1 综合评分矩阵

| 维度 | Python | TypeScript | Go | Rust |
|------|--------|------------|-----|------|
| **开发效率** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **运行效率** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **稳定性** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **RAG 生态** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **MCP SDK** | ✅ 官方 | ✅ 官方 | ✅ 官方 | ✅ 官方 |
| **Chroma 支持** | ✅ 原生 | ✅ 客户端 | ❌ 无官方 | ✅ 官方 |
| **模型生态** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| **学习曲线** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |

### 2.2 各语言深度分析

#### 🐍 Python

**优势**:
```
✅ RAG 生态最丰富
   - LangChain, LlamaIndex, Haystack
   - ChromaDB 原生 Python 支持
   
✅ 模型集成最简单
   - Ollama SDK (ollama Python 包)
   - OpenAI SDK (openai Python 包)
   - HuggingFace Transformers
   - llama-cpp-python
   
✅ FastAPI 成熟稳定
   - 原生异步支持
   - 自动 OpenAPI 文档
   - Pydantic 类型验证
   
✅ MCP 官方 SDK
   - modelcontextprotocol/python-sdk
   
✅ 开发速度最快
   - 快速迭代 MVP
   - 丰富的第三方库
```

**劣势**:
```
❌ 运行效率较低
   - 解释型语言
   - GIL 限制多线程
   
❌ 类型安全较弱
   - 虽然 mypy 可用，但非强制
   
❌ 内存占用较高
   - 相比编译型语言
```

**适用场景**: ✅ **HUB 定位项目的最佳选择**
- 需要丰富的适配器生态
- 多模型后端集成
- 快速迭代 MVP

---

#### 📘 TypeScript

**优势**:
```
✅ 前后端同语言
   - Vue 前端 + Node 后端
   - 类型定义可复用
   
✅ 类型安全强
   - 编译期类型检查
   - IDE 支持完善
   
✅ 异步模型好
   - Node.js 事件循环
   - 适合 I/O 密集型
   
✅ MCP 官方 SDK
   - @modelcontextprotocol/sdk
   
✅ Chroma 支持
   - chromadb-client 官方包
```

**劣势**:
```
❌ RAG 生态较弱
   - 不如 Python 丰富
   - 很多库需要自己封装
   
❌ 模型集成较繁琐
   - Ollama 需要手写 HTTP 调用
   - 本地模型支持有限
   
❌ CPU 密集型弱
   - 单线程限制
   - 大文件处理受限
```

**适用场景**:
- 前端团队主导
- 需要前后端代码复用
- 更看重类型安全

**与本项目匹配度**: ⚠️ 中等（RAG 生态不足是硬伤）

---

#### 🔵 Go

**优势**:
```
✅ 性能接近 Rust
   - 编译型语言
   - 并发模型优秀 (goroutine)
   
✅ 部署简单
   - 单二进制文件
   - 无运行时依赖
   
✅ 内存效率高
   - GC 但控制良好
   
✅ MCP 官方 SDK
   - modelcontextprotocol/go-sdk
```

**劣势**:
```
❌ Chroma 无官方支持
   - 需要自己封装 HTTP API
   - 增加开发工作量
   
❌ RAG 生态贫乏
   - 几乎所有库需要自己实现
   - 无 LangChain/LlamaIndex 等级库
   
❌ 模型集成困难
   - 需要手写大量适配器
   - 本地模型调用支持少
```

**适用场景**:
- 性能要求极高的服务
- 需要单二进制部署
- 团队有 Go 经验

**与本项目匹配度**: ❌ 不适合（生态不足，与 HUB 定位冲突）

**注**: rag-code-mcp 使用 Go，但它主要支持 Qdrant（非 Chroma），且功能相对单一。

---

#### 🦀 Rust

**优势**:
```
✅ 性能最高
   - 无 GC
   - 内存安全保证
   
✅ Chroma 官方支持
   - chromadb Rust crate
   
✅ 并发安全
   - 编译期保证
   - 无数据竞争
```

**劣势**:
```
❌ 开发效率最低
   - 学习曲线陡峭
   - 编译时间长
   
❌ 生态最贫乏
   - 几乎所有 RAG 组件需要自己造
   - 无成熟框架
   
❌ 人才稀缺
   - 招聘困难
   - 学习成本高
```

**适用场景**:
- 对性能有极致要求
- 有 Rust 团队
- 长期维护的核心组件

**与本项目匹配度**: ❌ 不适合 MVP（开发效率太低）

---

### 2.3 关键对比：生态支持

| 功能需求 | Python | TypeScript | Go | Rust |
|---------|--------|------------|-----|------|
| Chroma 集成 | ✅ 原生 | ✅ 客户端 | ⚠️ HTTP | ✅ 官方 |
| Qdrant 集成 | ✅ 官方 | ✅ 官方 | ✅ 官方 | ✅ 官方 |
| Ollama SDK | ✅ ollama | ⚠️ HTTP | ⚠️ HTTP | ⚠️ HTTP |
| OpenAI SDK | ✅ openai | ✅ openai | ⚠️ 社区 | ⚠️ 社区 |
| LangChain | ✅ 官方 | ⚠️ JS版 | ❌ 无 | ❌ 无 |
| LlamaIndex | ✅ 官方 | ⚠️ JS版 | ❌ 无 | ❌ 无 |
| sentence-transformers | ✅ 官方 | ❌ 无 | ❌ 无 | ❌ 无 |
| tree-sitter bindings | ✅ 成熟 | ✅ 成熟 | ⚠️ 社区 | ✅ 成熟 |

**结论**: Python 在 RAG/模型生态上具有压倒性优势。

---

## 三、核心结论

### 3.1 推荐方案

**✅ Python + FastAPI 是本项目的最佳选择**

### 3.2 决策依据

| 决策因素 | 分析 |
|---------|------|
| **HUB 定位** | 需要丰富生态支持多种模型后端，Python 生态最强 |
| **FastAPI 约束** | 已确认使用 FastAPI，锁定 Python |
| **Chroma 集成** | Python 原生支持，最简单 |
| **多模型支持** | Python SDK 覆盖 Ollama/OpenAI/llama.cpp/LM Studio |
| **MVP 速度** | Python 开发效率最高 |
| **MCP 协议** | Python 官方 SDK 支持 |

### 3.3 是否需要双语言架构？

#### 性能瓶颈分析

| 环节 | 瓶颈类型 | Python 能力 | 是否需要其他语言 |
|------|---------|------------|----------------|
| 文件解析 | I/O 密集 | ✅ asyncio 足够 | ❌ 不需要 |
| Embedding 调用 | 网络 I/O | ✅ asyncio 足够 | ❌ 不需要 |
| 向量检索 | 向量库处理 | ✅ Qdrant/Chroma 处理 | ❌ 不需要 |
| 结果排序 | CPU 密集 | ⚠️ 可能瓶颈 | 可选 Rust/Cython |
| 并发请求 | 网络 I/O | ✅ FastAPI async | ❌ 不需要 |

**结论**: 
- **MVP 阶段**: Python 足够，不需要双语言
- **Phase 2+**: 如遇性能瓶颈，可考虑 Rust/Cython 优化热点模块

#### 前后端语言问题

- 前端: Vue 3 + TypeScript
- 后端: Python + FastAPI

这是**经典组合**，无需统一语言。前后端分离架构下，语言不统一是常态。

---

## 四、模型后端抽象设计

### 4.1 设计原则

**核心定位**: 做 HUB，不固定模型

**设计目标**:
1. 支持多种本地模型后端（Ollama、llama.cpp、LM Studio）
2. 支持多种云端 API（OpenAI、Anthropic、Azure）
3. 支持自定义 HTTP 端点
4. 配置驱动，无需修改代码

### 4.2 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    EmbeddingProvider (抽象基类)                  │
├─────────────────────────────────────────────────────────────────┤
│  方法:                                                          │
│  ├── embed(texts: List[str]) -> List[List[float]]              │
│  ├── embed_single(text: str) -> List[float]                    │
│  ├── get_dimension() -> int                                     │
│  └── get_model_info() -> EmbeddingModelInfo                    │
├─────────────────────────────────────────────────────────────────┤
│  具体实现:                                                       │
│  ├── OllamaEmbeddingProvider      # 本地 Ollama                 │
│  ├── LlamaCppEmbeddingProvider    # llama.cpp 直接调用          │
│  ├── LMStudioEmbeddingProvider    # LM Studio API               │
│  ├── OpenAIEmbeddingProvider      # OpenAI API                  │
│  ├── AzureOpenAIEmbeddingProvider # Azure OpenAI                │
│  ├── AnthropicEmbeddingProvider   # Claude API (如支持)         │
│  ├── JinaEmbeddingProvider        # Jina AI API                 │
│  ├── CohereEmbeddingProvider      # Cohere API                  │
│  └── CustomHTTPEmbeddingProvider  # 自定义 HTTP 端点             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    RerankProvider (抽象基类)                     │
├─────────────────────────────────────────────────────────────────┤
│  方法:                                                          │
│  ├── rerank(query: str, docs: List[Document]) -> List[ScoredDoc]│
│  └── get_model_info() -> RerankModelInfo                        │
├─────────────────────────────────────────────────────────────────┤
│  具体实现:                                                       │
│  ├── CohereRerankProvider         # Cohere API                  │
│  ├── JinaRerankProvider           # Jina AI API                 │
│  ├── FlashRankRerankProvider      # flashrank 本地 (推荐)       │
│  ├── CrossEncoderRerankProvider   # sentence-transformers 本地  │
│  ├── OllamaRerankProvider         # Ollama 本地模型             │
│  └── CustomHTTPRerankProvider     # 自定义 HTTP 端点             │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    LLMProvider (抽象基类)                        │
├─────────────────────────────────────────────────────────────────┤
│  方法:                                                          │
│  ├── generate(prompt: str, **kwargs) -> str                     │
│  ├── generate_stream(prompt: str, **kwargs) -> AsyncIterator    │
│  └── get_model_info() -> LLMModelInfo                           │
├─────────────────────────────────────────────────────────────────┤
│  具体实现:                                                       │
│  ├── OllamaLLMProvider            # 本地 Ollama                 │
│  ├── LMStudioLLMProvider          # LM Studio                   │
│  ├── OpenAILLMProvider            # OpenAI API                  │
│  ├── AnthropicLLMProvider         # Claude API                  │
│  ├── AzureOpenAILLMProvider       # Azure OpenAI                │
│  └── CustomHTTPLLMProvider        # 自定义 HTTP 端点             │
└─────────────────────────────────────────────────────────────────┘
```

### 4.3 配置驱动设计

```yaml
# config.yaml
providers:
  embedding:
    default: ollama-bge
    
    instances:
      - name: ollama-bge
        type: ollama
        base_url: http://localhost:11434
        model: bge-m3
        dimension: 1024
        
      - name: ollama-nomic
        type: ollama
        base_url: http://localhost:11434
        model: nomic-embed-text
        dimension: 768
        
      - name: openai-small
        type: openai
        api_key: ${OPENAI_API_KEY}
        model: text-embedding-3-small
        dimension: 1536
        
      - name: openai-large
        type: openai
        api_key: ${OPENAI_API_KEY}
        model: text-embedding-3-large
        dimension: 3072
        
      - name: lmstudio-local
        type: http
        base_url: http://localhost:1234/v1
        model: nomic-embed-text
        dimension: 768
        
      - name: custom-endpoint
        type: http
        base_url: http://your-server:8080/embed
        headers:
          Authorization: Bearer ${CUSTOM_TOKEN}
        dimension: 1024

  rerank:
    default: flashrank
    
    instances:
      - name: flashrank
        type: flashrank
        model: ms-marco-MiniLM-L-12-v2
        
      - name: cohere
        type: cohere
        api_key: ${COHERE_API_KEY}
        model: rerank-english-v3.0
        
      - name: jina
        type: jina
        api_key: ${JINA_API_KEY}
        model: jina-reranker-v2-base-multilingual

  llm:
    default: ollama-qwen
    
    instances:
      - name: ollama-qwen
        type: ollama
        base_url: http://localhost:11434
        model: qwen2.5:7b
        
      - name: openai-gpt4
        type: openai
        api_key: ${OPENAI_API_KEY}
        model: gpt-4-turbo
        
      - name: claude
        type: anthropic
        api_key: ${ANTHROPIC_API_KEY}
        model: claude-3-sonnet-20240229
```

### 4.4 Provider 接口定义

```python
# providers/base.py
from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel

class EmbeddingModelInfo(BaseModel):
    name: str
    dimension: int
    max_tokens: int
    provider: str

class EmbeddingProvider(ABC):
    """Embedding 提供者抽象基类"""
    
    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        """批量生成嵌入向量"""
        pass
    
    @abstractmethod
    async def embed_single(self, text: str) -> List[float]:
        """单个文本生成嵌入向量"""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """获取向量维度"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> EmbeddingModelInfo:
        """获取模型信息"""
        pass


class RerankModelInfo(BaseModel):
    name: str
    provider: str
    max_sequence_length: int

class ScoredDocument(BaseModel):
    document: str
    score: float
    index: int

class RerankProvider(ABC):
    """Rerank 提供者抽象基类"""
    
    @abstractmethod
    async def rerank(
        self, 
        query: str, 
        documents: List[str],
        top_k: Optional[int] = None
    ) -> List[ScoredDocument]:
        """对文档进行重排序"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> RerankModelInfo:
        """获取模型信息"""
        pass
```

---

## 五、代码切分插件化设计

### 5.1 设计原则

**策略**: 滞后考虑 AST，作为可选插件

**理由**:
1. MVP 阶段快速实现，简单切分覆盖所有语言
2. AST 切分需要语言特定解析器，开发成本高
3. 作为插件，用户可按需安装

### 5.2 架构设计

```
┌─────────────────────────────────────────────────────────────────┐
│                    ChunkerPlugin (抽象基类)                      │
├─────────────────────────────────────────────────────────────────┤
│  方法:                                                          │
│  ├── chunk(content: str, language: str) -> List[Chunk]         │
│  ├── supported_languages() -> List[str]                         │
│  └── get_priority() -> int  # 插件优先级                        │
├─────────────────────────────────────────────────────────────────┤
│  内置实现 (MVP):                                                 │
│  ├── SimpleChunker          # 按字符数切分（默认后备）          │
│  ├── LineChunker            # 按行数切分                        │
│  ├── SentenceChunker        # 按句子切分（NLP）                  │
│  └── MarkdownChunker        # Markdown 标题切分                 │
├─────────────────────────────────────────────────────────────────┤
│  可选插件 (Phase 2):                                             │
│  │                                                              │
│  │  pip install coderag-treesitter                             │
│  │                                                              │
│  └── TreeSitterChunker      # AST 感知切分（15+ 语言）          │
│      ├── Python                                             │
│      ├── TypeScript / JavaScript                            │
│      ├── Go                                                 │
│      ├── Rust                                               │
│      ├── Java                                               │
│      ├── C / C++                                            │
│      └── ...                                                │
└─────────────────────────────────────────────────────────────────┘
```

### 5.3 Chunker 接口定义

```python
# chunkers/base.py
from abc import ABC, abstractmethod
from typing import List, Optional
from pydantic import BaseModel

class Chunk(BaseModel):
    """代码块"""
    content: str
    start_line: int
    end_line: int
    language: str
    metadata: dict = {}  # 额外元数据

class ChunkerPlugin(ABC):
    """代码切分插件抽象基类"""
    
    @abstractmethod
    def chunk(
        self, 
        content: str, 
        language: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[Chunk]:
        """将代码切分为块"""
        pass
    
    @abstractmethod
    def supported_languages(self) -> List[str]:
        """返回支持的语言列表，空列表表示支持所有语言"""
        pass
    
    def get_priority(self) -> int:
        """优先级，数字越大优先级越高"""
        return 0
    
    def can_handle(self, language: str) -> bool:
        """判断是否能处理该语言"""
        supported = self.supported_languages()
        return len(supported) == 0 or language.lower() in supported
```

### 5.4 内置 Chunker 实现

```python
# chunkers/simple.py
from .base import ChunkerPlugin, Chunk
from typing import List

class SimpleChunker(ChunkerPlugin):
    """简单字符数切分器 - 默认后备方案"""
    
    def chunk(
        self, 
        content: str, 
        language: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[Chunk]:
        chunks = []
        lines = content.split('\n')
        
        current_chunk = []
        current_size = 0
        start_line = 0
        
        for i, line in enumerate(lines):
            line_size = len(line) + 1  # +1 for newline
            
            if current_size + line_size > chunk_size and current_chunk:
                # 保存当前块
                chunks.append(Chunk(
                    content='\n'.join(current_chunk),
                    start_line=start_line,
                    end_line=i - 1,
                    language=language
                ))
                
                # 处理重叠
                overlap_lines = []
                overlap_size = 0
                for j in range(len(current_chunk) - 1, -1, -1):
                    if overlap_size >= overlap:
                        break
                    overlap_lines.insert(0, current_chunk[j])
                    overlap_size += len(current_chunk[j])
                
                current_chunk = overlap_lines
                current_size = overlap_size
                start_line = i - len(overlap_lines)
            
            current_chunk.append(line)
            current_size += line_size
        
        # 最后一块
        if current_chunk:
            chunks.append(Chunk(
                content='\n'.join(current_chunk),
                start_line=start_line,
                end_line=len(lines) - 1,
                language=language
            ))
        
        return chunks
    
    def supported_languages(self) -> List[str]:
        return []  # 支持所有语言
    
    def get_priority(self) -> int:
        return 0  # 最低优先级，作为后备


# chunkers/markdown.py
class MarkdownChunker(ChunkerPlugin):
    """Markdown 标题切分器"""
    
    def chunk(
        self, 
        content: str, 
        language: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[Chunk]:
        lines = content.split('\n')
        chunks = []
        
        current_section = []
        current_start = 0
        current_header = None
        
        for i, line in enumerate(lines):
            # 检测标题
            if line.startswith('#'):
                # 保存前一个 section
                if current_section:
                    chunks.append(Chunk(
                        content='\n'.join(current_section),
                        start_line=current_start,
                        end_line=i - 1,
                        language=language,
                        metadata={'header': current_header}
                    ))
                current_section = [line]
                current_start = i
                current_header = line
            else:
                current_section.append(line)
        
        # 最后一个 section
        if current_section:
            chunks.append(Chunk(
                content='\n'.join(current_section),
                start_line=current_start,
                end_line=len(lines) - 1,
                language=language,
                metadata={'header': current_header}
            ))
        
        return chunks
    
    def supported_languages(self) -> List[str]:
        return ['markdown', 'md']
    
    def get_priority(self) -> int:
        return 10  # Markdown 专用，优先级较高
```

### 5.5 Chunker 注册与调度

```python
# chunkers/registry.py
from typing import List, Dict, Type, Optional
from .base import ChunkerPlugin, Chunk

class ChunkerRegistry:
    """Chunker 插件注册中心"""
    
    def __init__(self):
        self._chunkers: Dict[str, ChunkerPlugin] = {}
        self._default_chunker: Optional[ChunkerPlugin] = None
    
    def register(self, chunker: ChunkerPlugin) -> None:
        """注册 chunker"""
        key = chunker.__class__.__name__
        self._chunkers[key] = chunker
        
        # 设置默认后备
        if chunker.get_priority() == 0 and self._default_chunker is None:
            self._default_chunker = chunker
    
    def get_chunker(self, language: str) -> ChunkerPlugin:
        """获取最适合该语言的 chunker"""
        candidates = [
            (c, c.get_priority()) 
            for c in self._chunkers.values() 
            if c.can_handle(language)
        ]
        
        if not candidates:
            return self._default_chunker
        
        # 返回优先级最高的
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    def chunk(
        self, 
        content: str, 
        language: str,
        **kwargs
    ) -> List[Chunk]:
        """自动选择 chunker 并切分"""
        chunker = self.get_chunker(language)
        return chunker.chunk(content, language, **kwargs)


# 全局注册中心
registry = ChunkerRegistry()

# 注册内置 chunkers
registry.register(SimpleChunker())
registry.register(MarkdownChunker())
```

### 5.6 Tree-sitter 插件（Phase 2）

```python
# 可选安装: pip install coderag-treesitter

# chunkers/treesitter.py
from .base import ChunkerPlugin, Chunk
from typing import List
import tree_sitter_python as tspython
import tree_sitter_typescript as tstypescript
import tree_sitter_go as tsgo
# ... 其他语言

class TreeSitterChunker(ChunkerPlugin):
    """AST 感知切分器"""
    
    LANGUAGE_MAP = {
        'python': tspython,
        'typescript': tstypescript.typescript,
        'javascript': tstypescript.tsx,
        'go': tsgo,
        # ...
    }
    
    # 节点类型 -> 语义单元
    CHUNK_NODE_TYPES = {
        'python': ['function_definition', 'class_definition', 'async_function_definition'],
        'typescript': ['function_declaration', 'class_declaration', 'method_definition', 'interface_declaration'],
        'go': ['function_declaration', 'method_declaration', 'type_declaration'],
        # ...
    }
    
    def chunk(
        self, 
        content: str, 
        language: str,
        chunk_size: int = 500,
        overlap: int = 50
    ) -> List[Chunk]:
        parser = self._get_parser(language)
        tree = parser.parse(bytes(content, 'utf8'))
        
        chunks = []
        node_types = self.CHUNK_NODE_TYPES.get(language, [])
        
        for node in self._traverse(tree.root_node):
            if node.type in node_types:
                chunks.append(Chunk(
                    content=content[node.start_byte:node.end_byte],
                    start_line=node.start_point[0],
                    end_line=node.end_point[0],
                    language=language,
                    metadata={
                        'node_type': node.type,
                        'name': self._extract_name(node, content)
                    }
                ))
        
        return chunks
    
    def supported_languages(self) -> List[str]:
        return list(self.LANGUAGE_MAP.keys())
    
    def get_priority(self) -> int:
        return 100  # 最高优先级
```

---

## 六、最终技术栈

### 6.1 技术栈总览

```
┌─────────────────────────────────────────────────────────────────┐
│                        技术栈总览                                │
├─────────────────────────────────────────────────────────────────┤
│  前端                                                           │
│  ├── 框架: Vue 3 + TypeScript                                  │
│  ├── UI 库: shadcn-vue                                        │
│  └── 状态管理: Pinia                                           │
├─────────────────────────────────────────────────────────────────┤
│  后端                                                           │
│  ├── 语言: Python 3.11+                                        │
│  ├── 框架: FastAPI                                             │
│  ├── 异步: asyncio + httpx                                     │
│  └── 验证: Pydantic v2                                         │
├─────────────────────────────────────────────────────────────────┤
│  协议层                                                         │
│  └── MCP: modelcontextprotocol/python-sdk                      │
├─────────────────────────────────────────────────────────────────┤
│  向量存储                                                       │
│  ├── MVP: Chroma (已安装)                                      │
│  └── Phase 2: Qdrant (生产环境)                                │
├─────────────────────────────────────────────────────────────────┤
│  模型抽象                                                       │
│  ├── Embedding: Provider 接口 (Ollama/OpenAI/HTTP/etc)         │
│  ├── Rerank: Provider 接口 (FlashRank/Cohere/etc)              │
│  └── LLM: Provider 接口 (Ollama/OpenAI/Claude/etc)             │
├─────────────────────────────────────────────────────────────────┤
│  代码切分                                                       │
│  ├── MVP: 简单字符切分 (支持所有语言)                           │
│  └── Phase 2: Tree-sitter 插件 (AST 感知)                      │
├─────────────────────────────────────────────────────────────────┤
│  部署                                                           │
│  ├── MVP: Docker Compose                                       │
│  └── 企业版: Kubernetes                                        │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 依赖清单（MVP）

```toml
# pyproject.toml

[project]
name = "coderag-hub"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    # Web 框架
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    
    # MCP
    "modelcontextprotocol>=0.1.0",
    
    # 向量数据库
    "chromadb>=0.4.22",
    
    # 模型 SDK
    "ollama>=0.1.0",
    "openai>=1.12.0",
    "httpx>=0.26.0",
    
    # Rerank
    "flashrank>=0.2.0",
    
    # 工具库
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "python-dotenv>=1.0.0",
    "PyYAML>=6.0.0",
    "watchdog>=4.0.0",  # 文件监听
    
    # 可选: Tree-sitter (Phase 2)
    # "tree-sitter>=0.21.0",
    # "tree-sitter-python>=0.21.0",
    # "tree-sitter-typescript>=0.21.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "ruff>=0.2.0",
    "mypy>=1.8.0",
]

treesitter = [
    "tree-sitter>=0.21.0",
    "tree-sitter-python>=0.21.0",
    "tree-sitter-typescript>=0.21.0",
    "tree-sitter-go>=0.21.0",
]
```

### 6.3 项目结构

```
coderag-hub/
├── backend/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI 入口
│   │   ├── config.py               # 配置管理
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py           # REST API 路由
│   │   │   └── websocket.py        # WebSocket 实时推送
│   │   │
│   │   ├── mcp/
│   │   │   ├── __init__.py
│   │   │   ├── server.py           # MCP Server 实现
│   │   │   └── tools/
│   │   │       ├── search_code.py
│   │   │       ├── get_context.py
│   │   │       └── index_workspace.py
│   │   │
│   │   ├── providers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Provider 抽象基类
│   │   │   ├── embedding/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── ollama.py
│   │   │   │   ├── openai.py
│   │   │   │   └── http.py
│   │   │   ├── rerank/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── flashrank.py
│   │   │   │   └── cohere.py
│   │   │   └── llm/
│   │   │       ├── __init__.py
│   │   │       ├── ollama.py
│   │   │       └── openai.py
│   │   │
│   │   ├── chunkers/
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Chunker 抽象基类
│   │   │   ├── registry.py         # 插件注册中心
│   │   │   ├── simple.py           # 简单切分
│   │   │   ├── line.py             # 行切分
│   │   │   └── markdown.py         # Markdown 切分
│   │   │
│   │   ├── storage/
│   │   │   ├── __init__.py
│   │   │   ├── chroma_store.py     # Chroma 向量存储
│   │   │   └── metadata.py         # 元数据存储
│   │   │
│   │   └── index/
│   │       ├── __init__.py
│   │       ├── indexer.py          # 索引器
│   │       └── watcher.py          # 文件监听
│   │
│   ├── tests/
│   ├── pyproject.toml
│   └── config.yaml
│
├── frontend/
│   ├── src/
│   │   ├── App.vue
│   │   ├── main.ts
│   │   ├── components/
│   │   ├── views/
│   │   └── stores/
│   ├── package.json
│   └── vite.config.ts
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yaml
│
├── docs/
│   └── README.md
│
└── README.md
```

---

## 七、待确认事项

### 7.1 技术决策待确认

| 问题 | 当前建议 | 需要确认 |
|------|---------|---------|
| **后端语言** | Python | ✅ 已确认 FastAPI |
| **是否双语言** | 否（MVP 不需要） | ⚠️ 待确认 |
| **前端框架** | Vue 3 + shadcn-vue | ⚠️ 待确认 |
| **向量数据库** | Chroma (MVP) → Qdrant (Phase 2) | ✅ 已确认 |
| **Tree-sitter** | Phase 2 插件 | ✅ 已确认 |

### 7.2 运维决策待确认

| 问题 | 建议方案 | 需要确认 |
|------|---------|---------|
| **部署方式** | Docker Compose | ⚠️ 待确认 |
| **存储持久化** | Docker Volume | ⚠️ 待确认 |
| **日志方案** | 结构化日志 + 文件 | ⚠️ 待确认 |
| **监控方案** | Phase 2 考虑 | ⚠️ 待确认 |

### 7.3 业务决策待确认

| 问题 | 建议方案 | 需要确认 |
|------|---------|---------|
| **支持的文件类型** | MVP: .py, .ts, .js, .md | ⚠️ 待确认 |
| **最大文件大小** | 默认 1MB | ⚠️ 待确认 |
| **默认切分参数** | 500 字符, 50 重叠 | ⚠️ 待确认 |
| **默认 Embedding** | Ollama bge-m3 | ⚠️ 待确认 |

---

## 附录

### A. 关键依赖版本锁定

```
# requirements.txt (生产环境)
fastapi==0.109.2
uvicorn[standard]==0.27.1
chromadb==0.4.22
modelcontextprotocol==0.1.0
ollama==0.1.6
openai==1.12.0
httpx==0.26.0
flashrank==0.2.5
pydantic==2.6.1
pydantic-settings==2.1.0
python-dotenv==1.0.1
PyYAML==6.0.1
watchdog==4.0.0
```

### B. 环境变量模板

```bash
# .env.example

# 服务配置
APP_ENV=development
APP_HOST=0.0.0.0
APP_PORT=8000

# Chroma 配置
CHROMA_PERSIST_DIR=./data/chroma

# Ollama 配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_EMBEDDING_MODEL=bge-m3
OLLAMA_LLM_MODEL=qwen2.5:7b

# OpenAI 配置 (可选)
OPENAI_API_KEY=sk-xxx
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_LLM_MODEL=gpt-4-turbo

# Cohere 配置 (可选，用于 Rerank)
COHERE_API_KEY=xxx

# Jina 配置 (可选，用于 Rerank)
JINA_API_KEY=xxx
```

### C. Docker Compose 模板

```yaml
# docker-compose.yaml
version: '3.8'

services:
  coderag-hub:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./config.yaml:/app/config.yaml
    environment:
      - APP_ENV=production
      - OLLAMA_BASE_URL=http://host.docker.internal:11434
    extra_hosts:
      - "host.docker.internal:host-gateway"
    restart: unless-stopped

  # 可选: Qdrant (Phase 2)
  # qdrant:
  #   image: qdrant/qdrant:latest
  #   ports:
  #     - "6333:6333"
  #   volumes:
  #     - ./data/qdrant:/qdrant/storage
```

---

**文档结束**

*本文档由 OpenCode AI 于 2026-03-19 生成，用于 Code-RAG Hub 项目技术选型决策参考。*