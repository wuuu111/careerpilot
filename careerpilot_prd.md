# CareerPilot 开发需求文档

## 1. 项目名称

**CareerPilot：基于 Multi-Agent Workflow 的 AI 求职申请助手平台**

---

## 2. 项目背景

当前学生和求职者在申请 AI、软件工程、数据科学、Agent 开发等岗位时，需要反复完成简历修改、岗位 JD 分析、Cover Letter 撰写、面试准备和投递记录管理。这些任务重复性强，但又需要结合个人经历、公司背景、岗位要求和技术栈进行个性化调整。

本项目希望构建一个基于 LLM Agent 的智能求职助手，通过 **RAG、Tool Calling、多智能体编排、结构化输出校验和生成质量评估**，实现从岗位分析到申请材料生成的一站式自动化流程。

该项目定位为一个面向 Agent 开发岗的工程化项目，重点体现：

- 多智能体工作流设计能力；
- RAG 知识库构建能力；
- Tool Calling 和外部工具集成能力；
- FastAPI 后端工程能力；
- 数据库建模和版本管理能力；
- Agent 执行过程可观测性；
- 生成内容质量评估与安全约束能力。

---

## 3. 项目目标

系统需要支持以下核心目标：

1. 用户可以上传 PDF / DOCX 格式简历；
2. 用户可以输入或上传目标岗位 JD；
3. 系统自动解析简历并结构化存储；
4. 系统自动分析岗位职责、技能要求和关键词；
5. 系统生成简历与岗位的匹配度报告；
6. 系统自动改写简历项目经历；
7. 系统生成个性化 Cover Letter；
8. 系统生成面试准备问题和复习计划；
9. 系统对生成内容进行质量评估；
10. 系统保存每次申请记录和生成版本；
11. 系统支持前端可视化展示 Agent 执行流程；
12. 系统支持后续接入不同 LLM Provider，例如 OpenAI、Qwen、DeepSeek 或阿里百炼。

---

## 4. 目标用户

### 4.1 普通用户

普通用户可以：

- 上传和管理简历；
- 输入目标岗位 JD；
- 查看岗位分析结果；
- 查看简历-JD 匹配报告；
- 生成简历优化建议；
- 生成 Cover Letter；
- 生成面试准备材料；
- 管理不同岗位的申请记录；
- 查看历史生成版本。

### 4.2 管理员

管理员可以：

- 查看系统运行日志；
- 查看 Agent 执行失败记录；
- 管理 Prompt 模板；
- 调整模型 Provider 和模型参数；
- 查看任务执行耗时和错误信息；
- 管理用户数据和系统配置。

---

## 5. 核心功能模块

## 5.1 简历上传与解析模块

### 功能描述

用户上传 PDF / DOCX 格式简历，系统自动解析文本内容，并调用 LLM 抽取结构化信息。

### 输入

- PDF 简历；
- DOCX 简历；
- 用户补充说明，可选。

### 输出

```json
{
  "basic_info": {
    "name": "",
    "email": "",
    "phone": "",
    "location": ""
  },
  "education": [],
  "skills": [],
  "projects": [],
  "experience": [],
  "awards": []
}
```

### 技术要求

- 使用 PyMuPDF 或 pdfplumber 解析 PDF；
- 使用 python-docx 解析 DOCX；
- 使用 LLM 进行结构化抽取；
- 使用 Pydantic 校验输出格式；
- 解析失败时返回明确错误信息；
- 原始文本和结构化结果都需要存入数据库；
- 敏感信息不应直接打印到日志中。

---

## 5.2 岗位 JD 分析模块

### 功能描述

用户输入岗位 JD，系统自动抽取岗位名称、职责、硬性技能、加分项、业务方向和岗位关键词。

### 输入

```json
{
  "company_name": "ByteDance",
  "job_title": "AI Agent Developer Intern",
  "job_description": "..."
}
```

### 输出

```json
{
  "role_type": "AI Agent Developer",
  "responsibilities": [],
  "required_skills": [],
  "preferred_skills": [],
  "keywords": [],
  "business_scenario": "",
  "seniority_level": "intern"
}
```

### 技术要求

- 使用 LLM 进行结构化分析；
- 输出必须通过 Pydantic 校验；
- 岗位关键词需要用于后续匹配度计算；
- JD 原文和分析结果需要入库；
- 支持中英文 JD。

---

## 5.3 RAG 知识库模块

### 功能描述

系统需要将用户简历、项目经历、岗位 JD、公司信息、历史生成内容存入向量数据库，用于后续个性化生成。

### 数据来源

- 用户简历；
- 岗位 JD；
- 公司背景；
- 用户历史项目经历；
- 历史生成的 Cover Letter；
- 历史修改版本。

### 技术要求

- 文本切分使用 token-based chunking；
- 默认 chunk size 为 800 tokens；
- 默认 chunk overlap 为 100 tokens；
- Embedding 模型可以使用 OpenAI Embedding、BGE、Qwen Embedding；
- 向量数据库可以使用 ChromaDB 或 PostgreSQL + pgvector；
- 每个 chunk 需要保存 metadata。

### Chunk Metadata 示例

```json
{
  "user_id": "",
  "source_type": "resume | jd | company | generated_output",
  "source_id": "",
  "created_at": "",
  "version": ""
}
```

---

## 5.4 多智能体工作流模块

### 功能描述

使用 LangGraph 构建多智能体工作流，每个 Agent 负责一个独立任务。系统需要记录每个 Agent 的输入、输出、执行状态、耗时和错误信息。

### Agent 列表

| Agent 名称 | 职责 |
|---|---|
| ResumeParserAgent | 解析简历 |
| JDAnalyzerAgent | 分析岗位 |
| MatchingAgent | 计算匹配度 |
| PlannerAgent | 制定优化计划 |
| ResumeRewriteAgent | 改写简历 |
| CoverLetterAgent | 生成求职信 |
| InterviewPrepAgent | 生成面试准备材料 |
| EvaluationAgent | 评估生成质量 |

### Workflow 运行记录

```json
{
  "run_id": "",
  "user_id": "",
  "application_id": "",
  "status": "running | success | failed",
  "started_at": "",
  "finished_at": "",
  "steps": []
}
```

### Agent Step 记录

```json
{
  "step_id": "",
  "agent_name": "",
  "input": {},
  "output": {},
  "status": "success | failed",
  "latency_ms": 0,
  "error_message": ""
}
```

---

## 5.5 简历-JD 匹配模块

### 功能描述

系统根据简历内容和岗位 JD，生成匹配度评分和优化建议。

### 评分维度

| 维度 | 权重 |
|---|---:|
| 技术栈匹配度 | 30% |
| 项目经历相关度 | 30% |
| 岗位关键词覆盖度 | 20% |
| 业务场景匹配度 | 10% |
| 表达质量 | 10% |

### 输出示例

```json
{
  "overall_score": 82,
  "dimension_scores": {
    "technical_skills": 85,
    "project_relevance": 80,
    "keyword_coverage": 78,
    "business_fit": 85,
    "writing_quality": 82
  },
  "matched_keywords": [],
  "missing_keywords": [],
  "recommendations": []
}
```

---

## 5.6 简历改写模块

### 功能描述

系统根据岗位 JD 对用户项目经历进行改写，使其更贴近目标岗位。

### 约束条件

1. 不允许编造不存在的经历；
2. 不允许虚构公司、奖项、论文、指标；
3. 可以优化表达方式；
4. 可以突出已有技术细节；
5. 可以将普通描述改写为 STAR / Action-Impact 风格；
6. 对高风险改写内容需要标记 risk_level。

### 输出格式

```json
{
  "original_bullet": "",
  "rewritten_bullet": "",
  "reason": "",
  "risk_level": "low | medium | high"
}
```

---

## 5.7 Cover Letter 生成模块

### 功能描述

系统根据用户经历、岗位 JD 和公司背景生成个性化 Cover Letter。

### 支持风格

- concise；
- formal；
- student-like；
- technical；
- business-oriented。

### 输出

```json
{
  "cover_letter": "",
  "style": "student-like",
  "word_count": 250,
  "used_evidence": []
}
```

---

## 5.8 面试准备模块

### 功能描述

系统根据岗位 JD 和用户简历生成面试准备材料。

### 输出内容

1. HR 面试问题；
2. 技术面试问题；
3. 项目深挖问题；
4. 高频知识点；
5. 复习计划；
6. 标准回答思路。

### 输出示例

```json
{
  "hr_questions": [],
  "technical_questions": [],
  "project_deep_dive_questions": [],
  "review_plan": [],
  "model_answers": []
}
```

---

## 5.9 生成质量评估模块

### 功能描述

系统自动评估生成结果质量，避免内容虚构、表达过度 AI 化、岗位关键词覆盖不足等问题。

### 评估维度

| 指标 | 说明 |
|---|---|
| Faithfulness | 是否忠于用户原始经历 |
| JD Coverage | 是否覆盖岗位关键词 |
| Specificity | 是否具体、有工程细节 |
| Readability | 是否自然清晰 |
| Hallucination Risk | 是否存在虚构风险 |

### 输出

```json
{
  "faithfulness": 90,
  "jd_coverage": 85,
  "specificity": 80,
  "readability": 88,
  "hallucination_risk": "low",
  "suggestions": []
}
```

---

## 6. 系统 API 设计

## 6.1 上传简历

```http
POST /api/resumes/upload
```

请求：

```json
{
  "user_id": "string",
  "file": "binary"
}
```

响应：

```json
{
  "resume_id": "string",
  "status": "parsed",
  "parsed_result": {}
}
```

---

## 6.2 创建岗位申请

```http
POST /api/applications
```

请求：

```json
{
  "user_id": "string",
  "resume_id": "string",
  "company_name": "string",
  "job_title": "string",
  "job_description": "string"
}
```

响应：

```json
{
  "application_id": "string",
  "status": "created"
}
```

---

## 6.3 运行 Agent 工作流

```http
POST /api/agent-runs
```

请求：

```json
{
  "application_id": "string",
  "workflow_type": "full_application"
}
```

响应：

```json
{
  "run_id": "string",
  "status": "running"
}
```

---

## 6.4 获取匹配报告

```http
GET /api/applications/{application_id}/matching-report
```

响应：

```json
{
  "overall_score": 82,
  "dimension_scores": {},
  "recommendations": []
}
```

---

## 6.5 生成 Cover Letter

```http
POST /api/applications/{application_id}/cover-letter
```

请求：

```json
{
  "style": "student-like",
  "language": "en"
}
```

响应：

```json
{
  "cover_letter_id": "string",
  "content": "string"
}
```

---

## 6.6 获取 Agent 执行轨迹

```http
GET /api/agent-runs/{run_id}/steps
```

响应：

```json
{
  "run_id": "string",
  "steps": []
}
```

---

## 7. 数据库设计

## 7.1 users

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 7.2 resumes

```sql
CREATE TABLE resumes (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    file_name VARCHAR(255),
    raw_text TEXT,
    parsed_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 7.3 job_descriptions

```sql
CREATE TABLE job_descriptions (
    id UUID PRIMARY KEY,
    company_name VARCHAR(255),
    job_title VARCHAR(255),
    raw_text TEXT,
    parsed_json JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 7.4 applications

```sql
CREATE TABLE applications (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    resume_id UUID REFERENCES resumes(id),
    jd_id UUID REFERENCES job_descriptions(id),
    status VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 7.5 agent_runs

```sql
CREATE TABLE agent_runs (
    id UUID PRIMARY KEY,
    application_id UUID REFERENCES applications(id),
    workflow_type VARCHAR(100),
    status VARCHAR(50),
    started_at TIMESTAMP,
    finished_at TIMESTAMP
);
```

## 7.6 agent_steps

```sql
CREATE TABLE agent_steps (
    id UUID PRIMARY KEY,
    run_id UUID REFERENCES agent_runs(id),
    agent_name VARCHAR(100),
    input_json JSONB,
    output_json JSONB,
    status VARCHAR(50),
    latency_ms INT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 7.7 generated_outputs

```sql
CREATE TABLE generated_outputs (
    id UUID PRIMARY KEY,
    application_id UUID REFERENCES applications(id),
    output_type VARCHAR(100),
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 8. 前端页面设计

## 8.1 首页 Dashboard

展示内容：

- 总申请数量；
- 最近申请记录；
- 平均匹配分数；
- 最近生成的 Cover Letter；
- Agent 运行状态；
- 最近失败任务。

## 8.2 简历管理页

功能：

- 上传简历；
- 查看解析结果；
- 编辑结构化简历；
- 查看历史版本；
- 删除无效简历。

## 8.3 岗位分析页

功能：

- 输入 JD；
- 查看岗位关键词；
- 查看技能要求；
- 查看岗位类型；
- 查看缺失技能；
- 保存目标岗位。

## 8.4 匹配报告页

功能：

- 展示整体匹配分；
- 展示维度评分；
- 展示 matched keywords；
- 展示 missing keywords；
- 展示优化建议；
- 展示改写优先级。

## 8.5 生成结果页

功能：

- 查看改写后的简历 bullet points；
- 查看 Cover Letter；
- 查看面试问题；
- 查看生成质量评分；
- 支持一键复制；
- 支持保存版本。

## 8.6 Agent Trace 页面

功能：

- 展示每个 Agent 的执行状态；
- 展示输入输出；
- 展示耗时；
- 展示失败原因；
- 方便调试和展示工程能力。

---

## 9. 推荐技术栈

## 9.1 后端

| 模块 | 技术 |
|---|---|
| Web API | FastAPI |
| Agent 编排 | LangGraph |
| LLM 调用 | OpenAI API / Qwen / DeepSeek / 阿里百炼 |
| 数据校验 | Pydantic |
| 数据库 | PostgreSQL |
| 向量数据库 | ChromaDB / pgvector |
| 文档解析 | PyMuPDF / pdfplumber / python-docx |
| 异步任务 | Celery / Redis |
| 部署 | Docker + Docker Compose |
| 日志 | Loguru / OpenTelemetry |
| 测试 | Pytest |

## 9.2 前端

| 模块 | 技术 |
|---|---|
| 前端框架 | React / Next.js |
| UI | TailwindCSS |
| 状态管理 | Zustand |
| 请求 | Axios |
| 可视化 | Recharts |
| 文件上传 | Upload component |

---

## 10. 非功能需求

## 10.1 性能要求

- 单次 JD 分析响应时间小于 10 秒；
- 完整 Agent Workflow 在 60 秒内完成；
- 支持异步任务处理；
- 大文件上传限制为 10MB；
- 支持任务失败后的重试机制。

## 10.2 安全要求

- 用户数据隔离；
- API Key 不允许暴露到前端；
- 简历文件需要访问权限控制；
- 日志中不直接打印完整简历隐私信息；
- 对生成内容中的虚构风险进行标记；
- 支持删除用户上传文件和历史生成记录。

## 10.3 可维护性要求

- Agent 模块解耦；
- Prompt 模板独立管理；
- 支持替换不同 LLM Provider；
- 所有结构化输出使用 Pydantic 校验；
- 关键模块需要单元测试；
- 核心 API 需要 Swagger 文档；
- 数据库迁移使用 Alembic 管理。

---

## 11. 推荐开发阶段

## Phase 1：MVP 版本

目标：做出可展示版本。

功能：

- 简历上传解析；
- JD 分析；
- 匹配报告；
- 简历 bullet 改写；
- Cover Letter 生成；
- PostgreSQL 存储；
- FastAPI 后端；
- 简单 React 前端。

## Phase 2：Agent Workflow 版本

目标：体现 Agent 开发能力。

新增：

- LangGraph 工作流；
- Agent Trace；
- 多 Agent 编排；
- EvaluationAgent；
- Prompt 模板管理；
- 错误处理和重试机制。

## Phase 3：RAG 增强版本

目标：体现 RAG 和长期记忆能力。

新增：

- ChromaDB / pgvector；
- 用户历史经历检索；
- 公司背景检索；
- 生成内容溯源；
- 历史版本对比。

## Phase 4：工程化部署版本

目标：用于简历和面试展示。

新增：

- Docker Compose；
- Redis + Celery；
- CI/CD；
- 单元测试；
- API 文档；
- Demo 视频；
- README；
- 部署到云服务器 / Render / Railway / 阿里云。

---

## 12. 简历展示建议

项目在简历中建议命名为：

**CareerPilot: Multi-Agent AI Career Application Assistant**

推荐英文描述：

- Designed and implemented a multi-agent AI application platform for resume-JD matching, resume rewriting, cover letter generation, and interview preparation targeting AI and software engineering roles.
- Built a modular Agent workflow with FastAPI and LangGraph, coordinating ResumeParserAgent, JDAnalyzerAgent, MatchingAgent, ResumeRewriteAgent, and EvaluationAgent with tool calling and traceable intermediate states.
- Developed a RAG pipeline to index resumes, project experiences, job descriptions, company profiles, and historical outputs into ChromaDB / pgvector for personalized and grounded content generation.
- Defined structured output schemas with Pydantic to validate LLM-generated resume parsing results, JD analysis, matching reports, and evaluation feedback.
- Implemented an automatic quality evaluation module measuring JD keyword coverage, factual consistency, specificity, readability, and hallucination risk.
- Stored application records, Agent execution traces, prompt versions, and generated artifacts in PostgreSQL, enabling version control, result comparison, and workflow observability.

---

## 13. README 结构建议

```markdown
# CareerPilot: Multi-Agent AI Career Application Assistant

## Overview

## Features
- Resume parsing
- JD analysis
- Resume-JD matching
- Resume rewriting
- Cover letter generation
- Interview preparation
- Agent trace visualization
- RAG-based personalization

## Tech Stack
- FastAPI
- LangGraph
- PostgreSQL
- ChromaDB / pgvector
- React
- Docker
- OpenAI / Qwen / DeepSeek API

## System Architecture

## Agent Workflow

## Database Schema

## API Documentation

## Demo Screenshots

## Evaluation Metrics

## Deployment Guide

## Future Improvements
```

---

## 14. 验收标准

项目完成后至少需要满足以下标准：

1. 用户可以成功上传并解析一份 PDF 简历；
2. 用户可以输入一个岗位 JD 并得到结构化岗位分析；
3. 系统可以生成简历-JD 匹配分数；
4. 系统可以给出至少 5 条简历优化建议；
5. 系统可以生成一版英文 Cover Letter；
6. 系统可以生成技术面试题和项目深挖问题；
7. 系统可以展示每个 Agent 的运行状态和中间输出；
8. 系统可以保存申请记录和生成历史；
9. 后端 API 可以通过 Swagger 页面测试；
10. 项目可以通过 Docker Compose 一键启动。

---

## 15. 项目价值总结

CareerPilot 不是一个简单的聊天机器人，而是一个具备任务规划、工具调用、知识检索、结构化输出、质量评估和运行轨迹可视化的 Agent 应用平台。该项目能够充分体现 Agent 开发岗所关注的核心能力，包括：

- LLM 应用开发；
- Multi-Agent Workflow；
- RAG Pipeline；
- Tool Calling；
- 后端工程实现；
- 数据库设计；
- 生成质量评估；
- Agent Observability；
- 工程化部署。
