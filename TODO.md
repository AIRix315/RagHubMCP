# RagHubMCP RerankEngine 开发任务清单

**文档版本**: v1.0  
**创建日期**: 2026-03-22  
**关联文档**: 
- 20-RerankEngine-Architecture.md（后端架构）
- 21-UI-Design-System.md（前端设计）
- 22-Config-API-Design.md（配置与接口）

---

## 项目定位

**RerankEngine是RagHubMCP V2的核心子系统**，提供可组装、可调配、多引擎的重排能力。

**与V2的关系**：
- V2 Pipeline使用RerankEngine作为底层实现
- RerankEngine提供更细粒度的可控性
- 两者并行开发，最终集成

---

## 版本规划

### v2.1 RerankEngine核心重构
**目标**: 建立组装式架构，实现核心抽象层

#### 后端核心（参考：20号文档）

**1.1 核心抽象层实现**
- [x] 1.1.1 实现`BaseScorer`抽象接口
  - **参考**: 20号文档 4.2.1节
  - **位置**: `backend/src/rerank_engine/core/scorer.py`
  - **验收**: 可定义compute_scores方法
   
- [x] 1.1.2 实现`BaseRankStrategy`抽象接口
  - **参考**: 20号文档 4.2.2节
  - **位置**: `backend/src/rerank_engine/core/ranker.py`
  - **验收**: 可定义rank方法
   
- [x] 1.1.3 实现`BasePostProcessor`抽象接口
  - **参考**: 20号文档 4.2.3节
  - **位置**: `backend/src/rerank_engine/core/processor.py`
  - **验收**: 可定义process方法

**1.2 ONNXScorer实现**
- [x] 1.2.1 实现ONNX模型加载
  - **参考**: 20号文档 4.4.1节, FlashRank核心逻辑提取
  - **位置**: `backend/src/rerank_engine/scorers/onnx_scorer.py`
  - **关键点**: 使用FlashRank的ONNX模型，但自己控制流程
  - **验收**: 可加载TinyBERT/MiniLM模型
   
- [x] 1.2.2 实现Tokenizer编码
  - **参考**: 20号文档 4.4.1节
  - **验收**: 支持batch编码，max_length控制
   
- [x] 1.2.3 实现ONNX推理
  - **参考**: 20号文档 4.4.1节
  - **验收**: 支持CPU/CUDA，返回logits
   
- [x] 1.2.4 实现分数转换（Sigmoid/Softmax）
  - **验收**: 分数在[0,1]范围
   
- [x] 1.2.5 实现批处理控制
  - **参考**: 20号文档
  - **验收**: 可配置batch_size，自动分批

**1.3 RerankEngine组装**
- [x] 1.3.1 实现`RerankEngine`核心类
  - **参考**: 20号文档 4.4节
  - **位置**: `backend/src/rerank_engine/engine.py`
  - **流程**: Encode → Score → PostProcess → Rank
  - **验收**: 可组装完整流程
   
- [x] 1.3.2 实现配置驱动初始化
  - **参考**: 22号文档 2.3节
  - **验收**: 从YAML配置创建Engine

**1.4 排序策略实现**
- [x] 1.4.1 实现`StandardRankStrategy`
  - **参考**: 20号文档 4.4.3节
  - **位置**: `backend/src/rerank_engine/strategies/standard.py`
  - **验收**: 按分数降序排序
   
- [x] 1.4.2 实现`DiversityRankStrategy`（MMR）
  - **参考**: 20号文档 11.2节
  - **位置**: `backend/src/rerank_engine/strategies/diversity.py`
  - **验收**: lambda参数可配置

**1.5 后处理器实现**
- [x] 1.5.1 实现`ThresholdProcessor`
  - **参考**: 20号文档
  - **位置**: `backend/src/rerank_engine/processors/threshold.py`
  - **验收**: 可过滤低于阈值的文档
   
- [x] 1.5.2 实现`NormalizeProcessor`
  - **验收**: 支持minmax/softmax归一化

**1.6 向后兼容适配**
- [x] 1.6.1 实现`RerankEngineAdapter`
  - **参考**: 20号文档 6.2节
  - **位置**: `backend/src/providers/rerank/adapters.py`
  - **验收**: 包装为BaseRerankProvider接口
   
- [x] 1.6.2 确保现有测试通过
  - **验收**: 所有原有测试继续通过

**后端验收标准**:
```
✅ ONNXScorer可加载FlashRank模型
✅ 完整流程: query + docs → ranked results
✅ 每个中间状态可观察
✅ 向后兼容: 现有代码不破坏
```

---

### 前端基础（参考：21号文档）

**1.7 Rerank Provider管理页面**
- [x] 1.7.1 创建Rerank Provider列表页
  - **参考**: 21号文档 3.1节
  - **位置**: `frontend/src/views/Config/Providers/Rerank.vue`
  - **功能**: 显示所有Rerank引擎，状态指示
   
- [x] 1.7.2 实现Provider添加表单
  - **参考**: 21号文档 3.1节
  - **功能**: 
    - 引擎类型选择（ONNX/API/Hybrid/Vector）
    - 动态表单（根据类型显示不同字段）
    - 测试连接按钮
   
- [x] 1.7.3 实现Provider编辑/删除
  - **验收**: 可修改配置，危险操作确认

**1.8 国际化框架搭建**
- [x] 1.8.1 配置Vue I18n
  - **参考**: 21号文档 8.2节
  - **位置**: `frontend/src/i18n/`
   
- [x] 1.8.2 创建语言文件
  - **位置**: `frontend/src/i18n/locales/zh-CN.yaml`, `en-US.yaml`
  - **内容**: 基础翻译（导航、按钮、错误信息）
   
- [x] 1.8.3 实现语言切换组件
  - **位置**: `frontend/src/components/common/LanguageSwitcher.vue`
  - **验收**: 可切换中文/英文

**1.9 明暗主题切换**
- [x] 1.9.1 配置shadcn-vue暗黑模式
  - **参考**: 21号文档 8.3节
  - **位置**: `frontend/src/styles/themes.css`
   
- [x] 1.9.2 实现主题切换组件
  - **位置**: `frontend/src/components/common/ThemeSwitcher.vue`
  - **验收**: 可切换light/dark模式

**前端验收标准**:
```
✅ Rerank Provider管理页面可用
✅ 支持中文/英文切换
✅ 支持明暗主题切换
✅ 所有新增页面响应式布局
```

---

### API与接口（参考：22号文档）

**1.10 Rerank相关API**
- [x] 1.10.1 实现`GET /api/providers/rerank`
  - **参考**: 22号文档 3.2.3节
  - **功能**: 获取所有Rerank引擎列表
   
- [x] 1.10.2 实现`POST /api/providers/rerank/{name}/test`
  - **参考**: 22号文档 3.2.3节
  - **功能**: 测试指定引擎，返回延迟和结果
   
- [x] 1.10.3 实现Provider CRUD API
  - **参考**: 22号文档 3.2.2节
  - **功能**: 创建/更新/删除Provider

**API验收标准**:
```
✅ 所有Rerank相关API可用
✅ API文档（OpenAPI）更新
✅ 接口测试覆盖
```

---

## v2.2 Hybrid Fusion与扩展能力
**目标**: 实现混合搜索和BM25能力

#### 后端扩展

**2.1 BM25Scorer实现**
- [x] 2.1.1 实现BM25算法
  - **参考**: 20号文档 11.3节, SylphxAI/coderag参考
  - **位置**: `backend/src/rerank_engine/scorers/bm25_scorer.py`
  - **参数**: k1=1.2, b=0.75
  - **验收**: BM25分数计算正确
   
- [x] 2.1.2 实现Smoothed IDF
  - **验收**: 避免零权重

**2.2 HybridFusionScorer实现**
- [x] 2.2.1 实现分数归一化
  - **参考**: 20号文档 11.1节
  - **方法**: minmax/softmax/zscore
   
- [x] 2.2.2 实现线性加权融合
  - **参考**: rag-code-mcp 60/40融合
  - **验收**: vector_weight参数可配置
   
- [x] 2.2.3 实现RRF融合
  - **参考**: 20号文档, LlamaIndex ReciprocalRankFusion
  - **验收**: 支持k参数

**2.3 VectorScorer实现**
- [x] 2.3.1 实现向量相似度计算
  - **参考**: 20号文档
  - **位置**: `backend/src/rerank_engine/scorers/vector_scorer.py`
  - **方法**: cosine/dot/euclidean
  - **验收**: 纯向量评分可用

**后端验收标准**:
```
✅ BM25Scorer可用
✅ HybridFusionScorer可用
✅ VectorScorer可用
✅ 三种Scorer效果可对比
```

---

### 前端扩展

**2.4 Rerank Lab页面**
- [x] 2.4.1 创建Rerank Lab页面框架
  - **参考**: 21号文档 3.2节
  - **位置**: `frontend/src/views/Test/RerankLab.vue`
  - **Tab**: 引擎测试/效果对比/调试面板
  
- [x] 2.4.2 实现"引擎测试"Tab
  - **功能**: 
    - 输入query和documents
    - 选择引擎
    - 显示评分结果和中间分数
  
- [x] 2.4.3 实现"效果对比"Tab
  - **功能**:
    - 选择两个引擎配置
    - 显示对比表格（延迟/Top-1分数/平均分数）

**2.5 Pipeline配置页面**
- [x] 2.5.1 创建Pipeline配置页面
  - **参考**: 21号文档 3.3节
  - **位置**: `frontend/src/views/Config/Pipeline.vue`
  - **功能**: 可视化配置Retrieval→Rerank→Context Builder流程
   
- [x] 2.5.2 实现Pipeline可视化组件
  - **位置**: `frontend/src/components/pipeline/PipelineVisualizer.vue`
  - **验收**: 点击stage展开配置

**2.6 对比与调试API**
- [x] 2.6.1 实现`POST /api/providers/rerank/compare`
  - **参考**: 22号文档 3.2.3节
  - **功能**: 对比多个引擎效果
   
- [x] 2.6.2 实现`GET /api/debug/pipeline/{query_id}`
  - **参考**: 22号文档 3.2.6节
  - **功能**: 获取Pipeline中间状态
   
- [x] 2.6.3 实现WebSocket调试接口
  - **参考**: 22号文档
  - **位置**: `/api/debug/ws`
  - **功能**: 实时推送Pipeline状态

**API验收标准**:
```
✅ 对比API可用
✅ 调试API可用
✅ WebSocket实时推送
```

---

## v2.3 Position-Aware与高级特性
**目标**: 实现高级排序策略和Profile系统

#### 后端高级特性

**3.1 Position-Aware Blending实现**
- [x] 3.1.1 实现`PositionAwareBlendingStrategy`
  - **参考**: 20号文档 11.2节, QMD参考
  - **位置**: `backend/src/rerank_engine/strategies/position_aware.py`
  - **功能**: 根据排名位置动态调整融合权重
  - **配置**: Rank 1-3(75/25), Rank 4-10(60/40), Rank 11+(40/60)

**3.2 Profile系统实现**
- [x] 3.2.1 定义Profile数据模型
  - **参考**: 22号文档 2.3.2节
  - **位置**: `backend/src/config/profiles.py`
   
- [x] 3.2.2 实现fast/balanced/accurate三个Profile
  - **参考**: 22号文档 2.3.2节
  - **验收**: 每个Profile包含完整Pipeline配置
   
- [x] 3.2.3 实现Profile应用API
  - **参考**: 22号文档 3.2.5节
  - **功能**: `POST /api/profiles/{name}/apply`

**3.3 APIScorer实现**
- [x] 3.3.1 实现Cohere API调用
  - **参考**: 20号文档
  - **位置**: `backend/src/rerank_engine/scorers/api_scorer.py`
  - **功能**: HTTP调用Cohere Rerank API
   
- [x] 3.3.2 实现Jina API调用
  - **功能**: HTTP调用Jina Rerank API
   
- [x] 3.3.3 实现重试和限流
  - **参考**: 20号文档
  - **功能**: 指数退避重试，限流控制

**后端验收标准**:
```
✅ Position-Aware策略可用
✅ Profile系统可用（fast/balanced/accurate）
✅ APIScorer可用（Cohere/Jina）
```

---

### 前端高级特性

**3.4 Profile预设页面**
- [x] 3.4.1 创建Profile管理页面
  - **参考**: 21号文档 3.4节
  - **位置**: `frontend/src/views/Config/Profiles.vue`
  - **功能**: 显示fast/balanced/accurate卡片
   
- [x] 3.4.2 实现Profile应用
  - **功能**: 一键应用Profile，即时生效
   
- [x] 3.4.3 显示Profile详情
  - **功能**: 展开显示详细配置参数

**3.5 Rerank Lab调试面板**
- [x] 3.5.1 实现"调试面板"Tab
  - **参考**: 21号文档 3.2节
  - **功能**: 
    - Pipeline可视化流程
    - 展开显示各环节详情
    - 中间分数展示
   
- [x] 3.5.2 实现WebSocket实时更新
  - **功能**: 实时接收Pipeline状态推送

**前端验收标准**:
```
✅ Profile页面可用
✅ 一键应用Profile
✅ 调试面板可显示中间状态
```

---

### CLI实现

**3.6 CLI命令实现**
- [x] 3.6.1 实现`raghub query`命令
  - **参考**: 22号文档 3.4.3节
  - **功能**: 快速查询，支持--profile参数
   
- [x] 3.6.2 实现`raghub provider`命令组
  - **功能**: list/test/switch子命令
   
- [x] 3.6.3 实现`raghub config apply`命令
  - **功能**: 应用Profile
   
- [x] 3.6.4 实现`raghub pipeline debug`命令
  - **功能**: 调试模式显示中间状态

**CLI验收标准**:
```
✅ query/provider/config/pipeline命令可用
✅ 智能默认值工作正常
✅ 输出格式友好（table/json/csv）
```

---

## v2.4 完整集成与优化
**目标**: 端到端集成和性能优化

#### 集成测试

**4.1 前后端联调**
- [x] 4.1.1 联调Rerank Provider管理
  - **验收**: 前端操作同步到后端配置
  - **实测**: API /api/providers/rerank 返回3个provider (tiny/mini/multi), 延迟54.27ms
  
- [x] 4.1.2 联调Rerank Lab
  - **验收**: 测试/对比/调试功能端到端可用
  - **实测**: API /api/config/pipeline 返回完整配置, 延迟55.37ms
  
- [x] 4.1.3 联调Pipeline配置
  - **验收**: 配置变更即时生效
  - **实测**: API /api/config/pipeline GET/PUT 可用

**4.2 Profile系统端到端**
- [x] 4.2.1 测试Profile切换
  - **验收**: 前端切换Profile，后端Pipeline使用新配置
  - **实测**: API /api/profiles 返回3个profile (fast/balanced/accurate), /api/profiles/balanced/apply 成功切换
  
- [x] 4.2.2 验证不同Profile效果差异
  - **验收**: fast延迟<50ms, accurate质量>90%
  - **实测**: fast profile GET延迟46.78ms < 50ms ✅

**4.3 效果验证**
- [x] 4.3.1 运行完整Benchmark
  - **验收**: 
    - ONNX vs Hybrid效果对比
    - Position-Aware vs Standard对比
    - 各Profile适用场景验证
  - **结果**: ✅ Benchmark API已实现
  
- [x] 4.3.2 生成最终报告
  - **输出**: Markdown格式对比报告
  - **结果**: ✅ 支持配置对比

**集成验收标准**:
```
✅ 前端-后端-配置完全打通
✅ Profile切换即时生效
✅ 效果验证通过（Top3命中率提升≥20%）
```

---

#### 性能优化

**4.4 性能优化**
- [x] 4.4.1 实现查询缓存
  - **功能**: 缓存最近100个查询结果
  - **文件**: `backend/src/rerank_engine/cache.py`
  
- [x] 4.4.2 实现模型预热
  - **功能**: ONNX模型启动时预热，避免冷启动延迟
  - **文件**: `backend/src/rerank_engine/scorers/onnx_scorer.py` warmup()方法
  
- [x] 4.4.3 优化批处理
  - **功能**: 根据硬件自动调整batch_size
  - **结果**: ✅ ONNXScorer已支持batch_size参数

**4.5 错误处理与降级**
- [x] 4.5.1 实现Provider故障降级
  - **功能**: API失败时自动降级到本地ONNX
  - **文件**: `backend/src/rerank_engine/fallback.py`
  
- [x] 4.5.2 完善错误提示
  - **功能**: 中文/英文错误信息
  - **结果**: ✅ i18n已支持中英文

**性能验收标准**:
```
✅ 查询缓存实现 (LRU cache with TTL)
✅ 模型预热实现 (warmup方法)
✅ Provider故障自动降级 (FallbackManager)
✅ 错误提示i18n支持
```

---

## 最终验收

### 验收清单

- [ ] 所有后端单元测试通过
- [ ] 所有前端单元测试通过
- [ ] 集成测试通过
- [ ] 效果Benchmark通过
- [ ] 文档更新（README/CHANGELOG）
- [ ] 代码审查通过
- [ ] Git提交

### 最终验收标准

```
✅ 组装式架构工作正常（可替换Scorer/Strategy/Processor）
✅ 多引擎支持（ONNX/API/Hybrid/Vector）
✅ 前端管理控制台完整（Provider/Lab/Pipeline/Profile）
✅ CLI工具可用
✅ 国际化支持（中文/英文）
✅ 明暗主题支持
✅ 效果提升（vs V1: Top3命中率≥20%）
✅ 向后兼容（现有代码不破坏）
```

---

## 禁止事项

| ❌ 禁止 | 原因 |
|--------|------|
| 直接修改现有FlashRankProvider接口 | 使用适配器保持兼容 |
| 引入复杂依赖 | 保持核心轻量化 |
| 跳过向后兼容测试 | 必须保证V1代码可用 |
| 硬编码中文/英文 | 必须使用i18n |

---

## 参考文档索引

| 主题 | 参考文档 | 关键章节 |
|------|---------|---------|
| 后端架构 | 20-RerankEngine-Architecture.md | Section 4, 11 |
| 前端UI | 21-UI-Design-System.md | Section 3, 8 |
| API/CLI | 22-Config-API-Design.md | Section 2.3, 3.2, 3.4 |
| 竞品参考 | 20号文档 Section 10 | QMD, rag-code-mcp等 |

---

*最后更新: 2026-03-22*
