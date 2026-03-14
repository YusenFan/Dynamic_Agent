# 1. System Overview

该系统是一个 **AI-driven execution orchestration system**，目标是将用户的一句自然语言目标转化为真实部署在线上的 web demo。

系统设计围绕四个核心理念：

**Execution-first architecture**

系统的成功标准不是生成建议或代码，而是完成真实部署并产生可访问的在线结果。

**Dynamic multi-agent architecture**

系统不会预定义固定 agent。所有 agent 都根据任务需求动态生成并销毁。

**Consensus-based orchestration**

Main Agent 不是单一模型，而是 **三个模型组成的 deliberation system**，通过讨论与共识确定系统决策。

**Secure-by-design data boundary**

AI 永远无法接触用户敏感信息（API key、token、secret）。AI 只生成变量名，由用户填写。

**Secure data boundary**

AI 永远无法读取用户 API key 或 secret。

**Markdown-native memory**

系统记忆以 `.md` 文件为主存储结构。

---

# 2. Core System Architecture

系统由以下主要层组成：

User Interface Layer

Main Agent Consensus Layer

Dynamic Agent Runtime

Adapter Interface Layer

Memory Layer (.md storage)

Execution Layer

Security Boundary Layer

整体逻辑：

用户输入目标 →  Main Agent → 生成 Task Graph-> 动态生成 Subagent-> Subagent 调用 Adapter-> 执行 CLI/API/MCP-> 部署-> 验证-> 交付 URL

# 3. Workspace Architecture

Workspace 是系统的 **最外层执行环境**。

Workspace 的职责是：

管理多个 project

生成 project configuration

管理 secret vault

提供统一 adapter registry

提供 memory storage root

Workspace 不执行任务，但提供运行基础设施。

3.1 Workspace Directory Structure

```
workspace/
```

包含：

```
workspace/
  projects/
  memory/
  adapters/
  vault/
  configs/
```

说明：

projects

所有项目

memory

项目 memory

adapters

可用 adapter

vault

secret storage

configs

workspace configuration

---

## 3.2 Workspace Responsibilities

Workspace 负责：

生成 Project

初始化 Project memory

生成 Project config

管理 adapter registry

管理 secret vault

Workspace 不参与 agent 推理。

---

# 4. Project Architecture

Project 是系统的 **任务执行容器**。

每个 project 对应一个用户目标。

---

## 4.1 Project Directory Structure

```
workspace/projects/project_x/
```

包含：

```
project_x/
  config.yaml
  task_graph.json
  agents/
  memory/
  artifacts/
  logs/
```

---

## 4.2 Project Configuration

Workspace 创建 project 时生成：

```
config.yaml
```

示例：

```
project_id: project_x
created_at: timestamp
status: active
supported_platforms:
  - vercel
  - supabase
default_models:
  planner: claude_opus
  critic: gemini_5_1_pro
  balancer: chatgpt_5_4
```

---

# 5. Main Agent Council Architecture

Main Agent 不是单模型。

它由三个不同模型组成：

Claude Opus

Gemini 5.1 Pro

ChatGPT-5.4

三者形成 **AI Council**。

---

## 5.1 Model Roles

### Planner

Model: **Claude Opus**

职责：

解析用户目标

生成计划

生成 task graph

建议 agent spawning

提出 execution strategy

Claude Opus 擅长长逻辑规划，因此担任 Planner。

---

### Critic

Model: **Gemini 5.1 Pro**

职责：

审查计划

识别漏洞

发现风险

提出 alternative plan

挑战 Planner 的假设

Critic 的目标是减少 hallucination 和错误路径。

---

### Balancer

Model: **ChatGPT-5.4**

职责：

综合 Planner 与 Critic

选择最终方案

生成 consensus result

更新 memory

推进状态机

Balancer 是 **最终决策整合者**。

---

## 5.2 Deliberation Protocol

每个关键决策执行如下流程：

Step 1

Planner 提出 plan

Step 2

Critic 评估 plan

Step 3

Planner 可回应 critic

Step 4

Balancer 选择最终方案

Step 5

更新 memory

---

## 5.3 Consensus Output Format

```
consensus_result:
  chosen_plan: ...
  rejected_plans: [...]
  reasoning_summary: ...
  risks: [...]
  agents_to_spawn: [...]
  decision_gate_required: true/false
  confidence: 0-1
```

---

# 6. Main Agent State Machine

Main Agent 状态机由 **Balancer 驱动**。

状态：

IDLE

INTAKE

PLANNING

ALLOCATING

EXECUTING

WAITING_FOR_USER_DECISION

RECOVERY_COORDINATION

VERIFYING

TERMINAL

---

## 状态说明

### IDLE

等待用户任务。

---

### INTAKE

解析用户输入。

输出：

project brief

---

### PLANNING

Council deliberation。

生成：

task graph

---

### ALLOCATING

spawn agents。

---

### EXECUTING

agent 执行任务。

---

### WAITING_FOR_USER_DECISION

Decision Gate。

---

### RECOVERY_COORDINATION

错误恢复。

---

### VERIFYING

部署验证。

---

### TERMINAL

任务结束。

---

# 7. Dynamic Agent Architecture

系统 agent **全部动态生成**。

不存在固定 agent pool。

---

## 7.1 Agent Spawn Rules

以下条件触发 agent：

独立权限

独立知识

独立状态

长期复用

错误恢复

---

## 7.2 Agent Object Schema

```
agent_id
project_id
agent_type
role_description
status
capabilities
knowledge_scope
private_memory_path
auth_variable_refs
active_tasks
spawn_reason
created_by
created_at
```

---

## 7.3 Agent Directory

```
project_x/agents/
```

例如：

```
agents/
  agent_research_01/
  agent_build_01/
  agent_vercel_01/
```

---

# 8. Memory Architecture (.md)

Memory 采用 Markdown。

原因：

LLM-friendly

Git-friendly

human-readable

---

## 8.1 Project Memory Directory

```
project_x/memory/
```

文件：

```
goals.md
constraints.md
decisions.md
resources.md
progress.md
risks.md
artifacts.md
```

---

## 8.2 Example goals.md

```
# Goals

Primary Goal:
Deploy a public web demo.

Secondary Goals:
Fast deployment
Minimal configuration
```

---

## 8.3 Agent Memory

路径：

```
agents/{agent_id}/memory/
```

文件：

```
knowledge.md
execution_patterns.md
failures.md
sessions.md
```

---

## 8.4 Scratchpad

```
/memory/scratchpad/
```

短期推理。

---

# 9. Secure Secret Handling

AI 永远不能访问 secret。

---

## 9.1 Principle

AI 可以：

生成 variable name

AI 不可以：

读取 secret

保存 secret

---

## 9.2 Example

AI 输出：

```
Required Variables:

VERCEL_API_TOKEN=
SUPABASE_API_KEY=
```

用户填写。

---

## 9.3 Vault Layer

secret 存储：

```
workspace/vault/
```

AI 只能看到：

```
vault_reference
```

例如：

```
vault://vercel/token
```

---

# 10. Adapter System

统一 external interface。

支持：

CLI

API

MCP

Skill

---

## Adapter Schema

```
adapter_id
platform
capabilities
auth_requirements
actions
```

---

# 11. Decision Gate Engine

Decision Gate 控制自动化边界。

---

## Trigger Conditions

Irreversible Action

Cost Bearing

External Authorization

Architecture Lock-in

Public Exposure

Multiple Trade-offs

Low Confidence

---

## Decision Packet

```
decision_topic
reason
options
recommended_option
pros_cons
cost_impact
risk
reversibility
```

---

# 12. Error Recovery

错误统一进入：

RECOVERY_COORDINATION

流程：

error classification

spawn recovery agent

retry execution

---

# 13. Example Execution Flow

用户：

“Create a demo for investors.”

流程：

Workspace 创建 project

↓

Council planning

↓

spawn ResearchAgent

↓

spawn BuildAgent

↓

Decision Gate (hosting)

↓

spawn VercelAgent

↓

deploy

↓

verify

↓

return URL

---

# 14. MVP Scope

支持：

dynamic agents

3-model orchestration

workspace-project structure

markdown memory

secure secret boundary

web demo deployment

---

# 15. v1 Non Goals

不支持：

multi-user collaboration

enterprise security policy

unlimited agent delegation

complex observability

fully autonomous deployments

---

# 16. Key System Innovations

三模型 deliberation orchestration

dynamic agent generation

workspace-project architecture

markdown-native memory

AI-safe secret boundary

execution-first AI system