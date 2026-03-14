
# 1. Task Graph Architecture

## 1.1 Why DAG

Task Graph 不能只是一个 checklist。

因为这个系统不是线性执行，而是需要：

支持并行

支持依赖

支持动态插入任务

支持用户决策阻塞

支持失败恢复

支持 agent 切换执行者

支持解释“为什么系统现在停在这里”

所以任务表示必须是 DAG，而不是简单数组。

---

## 1.2 DAG Design Principles

任务 DAG 必须满足以下原则：

第一，任务之间的依赖必须显式表达。

第二，任务节点状态必须独立可追踪。

第三，节点必须与“执行能力需求”绑定，而不是与固定 agent 绑定。

第四，图必须允许运行时扩展。

第五，图必须允许失败后局部恢复，而不是整个流程重来。

第六，图必须允许显式标记 Decision Gate 节点。

第七，图必须支持产物引用和 memory 引用。

---

## 1.3

.3 Task Node Schema

建议每个任务节点采用如下对象结构：

```
{
  "task_id":"task_hosting_selection",
  "project_id":"project_x",
  "name":"Select Hosting Platform",
  "task_type":"decision",
  "status":"pending",
  "priority":"high",
  "description":"Choose the hosting platform for deployment.",
  "dependencies": ["task_build_complete"],
  "dependency_type":"hard",
  "inputs": [
"memory://goals.md",
"memory://constraints.md",
"artifact://deployment_candidates"
  ],
  "outputs": [],
  "executor_requirement": {
    "agent_type":"hosting_agent",
    "capability_tags": ["hosting","deployment"]
  },
  "spawn_policy": {
    "spawn_if_missing":true,
    "reuse_existing_if_match":true
  },
  "decision_gate":true,
  "reversible":true,
  "retry_policy": {
    "max_retries":2
  },
  "artifact_contract": {
    "expected_outputs": ["hosting_choice"]
  },
  "created_by":"main_agent_council",
  "created_at":"timestamp"
}
```

这里最关键的是五个字段：

`dependencies`：决定执行先后

`executor_requirement`：告诉 scheduler 需要什么类型的 agent

`spawn_policy`：告诉 scheduler 是复用还是新建

`decision_gate`：标记是否必须停下来等用户

`artifact_contract`：明确此任务产出什么

---

## 1.4 Task Types

建议 v2 中固定一组有限 task type，避免 runtime 失控。

**analysis**

用于需求理解、约束提取、方案整理。

**research**

用于背景搜索、平台资料收集、文档理解。

**decision**

用于用户必须做选择的节点。

**build**

用于代码生成、项目骨架、页面实现。

**configure**

用于生成 env 模板、配置模板、集成准备。

**deploy**

用于真实部署。

**verify**

用于部署验证、链接验证、基础 smoke test。

**recover**

用于失败修复。

这些 task type 直接影响 scheduler 的调度策略和 adapter 调用策略。

---

## 1.5 Dependency Semantics

DAG 的边不能只表示“顺序”，还应表示依赖强度。建议分三类：

**hard dependency**

前置不完成，后置不能执行。

例如 deploy 依赖 build。

**soft dependency**

前置结果会提升质量，但不是强阻塞。

例如 background research 对 landing page wording 有帮助，但不一定要先完成。

**decision dependency**

前置是用户选择。未选择前不能继续。

例如 hosting platform 决策。

这样设计能避免系统过度僵硬。

---

## 1.6 Layered Graph

为了便于理解和调试，建议将任务图逻辑上分层：

**Discovery Layer**

分析需求、做 research。

**Design Layer**

整理方案、确定技术路径。

**Build Layer**

生成代码和项目骨架。

**Infra Layer**

部署平台、数据库、配置、环境变量。

**Validation Layer**

验证上线结果、输出交付物。

典型 demo deployment DAG 示例：

```
user_goal_intake
  → requirements_analysis
  → product_research
  → solution_outline
  → build_scaffold
  → generate_demo_code
  → choose_hosting
  → prepare_env_template
  → deploy_demo
  → verify_url
  → final_delivery
```

---

## 1.7 Runtime Graph Expansion

由于你的系统强调动态 agent 和动态执行，因此 DAG 必须支持运行时扩展。

例如：

如果用户选择 Supabase

→ 新增 `db_platform_selection`、`db_env_template`、`db_connection_setup`、`db_verification`

如果部署失败

→ 新增 `recover_build_config` 或 `recover_auth_binding`

如果某个 SaaS 插件暴露了新的前置要求

→ 新增配置任务节点

因此 Task Graph Engine 必须支持：

新增节点

新增边

重试节点

替换节点

归档节点

要求是：无论如何扩展，图都必须保持无环。

---

## 1.8 Task Node State Machine

每个节点建议使用以下状态：

`pending`

节点存在，但依赖未满足。

`ready`

依赖已满足，可以调度。

`running`

正在执行。

`blocked`

缺少外部资源、adapter、用户输入或运行条件。

`waiting_user`

进入 Decision Gate，等待用户。

`failed`

执行失败，但可恢复。

`completed`

成功完成。

`archived`

任务已被替代或不再活跃。

转移大致如下：

```
pending → ready → running → completed
running → failed
failed → ready
running → blocked
blocked → ready
running → waiting_user
waiting_user → ready
```

---

## 1.9 DAG Compilation by Council

任务 DAG 不由单一模型生成，而由 Main Agent Council 生成。

Claude Opus（Planner）

提出初版 DAG、阶段划分、主要节点。

Gemini 5.1 Pro（Critic）

检查 DAG 是否缺失依赖、是否有不合理顺序、是否遗漏风险节点。

ChatGPT-5.4（Balancer）

综合并产出最终 canonical DAG，写入 `task_graph.json`。

这样可以降低单模型规划错误。

---

# 2. Agent Runtime Scheduler

## 2.1 Scheduler Objective

Scheduler 是执行层的核心。

它负责把 “图中 ready 的任务” 分配给 “合适的动态 agent”。

它需要解决五件事：

第一，什么时候创建 agent。

第二，什么时候复用 agent。

第三，哪个任务先执行。

第四，任务阻塞或失败时怎么调整。

第五，任务完成后 agent 怎么处置。

---

## 2.2 Scheduler Inputs

Scheduler 的输入来自四部分：

当前 `task_graph.json`

当前项目 `runtime_state.json`

当前可用 agent 实例状态

当前 adapter / resource / vault reference 可用性

因此 scheduler 并不是只看 task ready 不 ready，它还要看系统是否具备执行条件。

---

## 2.3 Scheduler Core Loop

Scheduler 可以设计成事件驱动循环：

```
1. Scan graph for ready tasks
2. Rank tasks by priority + dependency criticality
3. Match task with existing agent
4. If no suitable agent and spawn allowed, create agent
5. Dispatch task
6. Collect task result / progress / failure
7. Update graph state
8. Trigger new ready tasks
9. Repeat
```

---

## 2.4 Scheduling Policy

建议 v2 采用简单但稳定的策略，而不是一开始追求最优调度。

排序依据可以是：

高优先级优先

阻塞后续关键路径的任务优先

Decision Gate 前置任务优先

恢复任务优先级略高于普通任务

验证任务优先保证闭环

也就是说，scheduler 更偏 **critical-path aware**，而不是简单 FIFO。

---

## 2.5 Agent Matching Logic

Scheduler 给任务找执行者时，优先顺序建议如下：

第一，复用已有 agent，如果它满足：

同项目

状态可运行

能力匹配

知识域匹配

当前负载允许

第二，如果无匹配 agent，则按 `spawn_policy` 动态生成新 agent。

第三，如果任务本身不需要独立权限/知识/状态，则不生成 agent，而由 Main Agent 直接调用 adapter 执行。

---

## 2.6 Dynamic Spawn Rules

系统没有固定 agent pool。

Scheduler 需要根据任务动态判断是否 spawn。

建议规则：

**必须新建 agent**

当任务需要独立平台状态、独立权限上下文、独立知识作用域时。

例如首次 Vercel 部署。

**优先复用 agent**

当已有 agent 在同项目内已掌握该平台状态。

例如第二次调用同一 Vercel agent。

**可直接执行，无需 agent**

当只是一次性低复杂度工具调用时。

例如读取某份公开文档。

---

## 2.7 Agent Execution Contract

Scheduler 给 agent 派任务时，输入不应是松散 prompt，而是标准执行包。

建议如下：

```
{
  "dispatch_id":"dispatch_001",
  "task_id":"task_deploy_demo",
  "project_id":"project_x",
  "agent_id":"agent_vercel_01",
  "task_summary":"Deploy the generated demo to Vercel",
  "input_refs": [
"artifact://source_code_bundle",
"memory://decisions.md",
"memory://resources.md"
  ],
  "expected_outputs": [
"deployment_url",
"deployment_status"
  ],
  "constraints": [
"AI cannot read secret values"
  ]
}
```

这样 agent runtime 更容易标准化。

---

## 2.8 Agent Return Contract

agent 执行后应返回结构化结果：

```
{
  "task_id":"task_deploy_demo",
  "agent_id":"agent_vercel_01",
  "status":"completed",
  "facts_discovered": [],
  "artifacts_produced": [
"artifact://deployment_url"
  ],
  "risks_detected": [],
  "followup_task_suggestions": [],
  "requires_decision_gate":false,
  "confidence":0.89
}
```

如果失败：

```
{
  "task_id":"task_deploy_demo",
  "agent_id":"agent_vercel_01",
  "status":"failed",
  "error_category":"config_missing",
  "recoverable":true,
  "suggested_recovery_task":"recover_env_binding"
}
```

---

## 2.9 Scheduler and Failure Handling

Scheduler 不直接修 bug，但要决定系统如何响应失败。

流程建议为：

任务失败

→ 标记节点 failed

→ 通知 Main Agent Council

→ Balancer 判断是否进入 recovery path

→ 如果可恢复，插入 recovery task

→ Scheduler 调度 recovery agent

→ recovery 完成后原任务重新进入 ready

这意味着 **recovery 不是特殊逻辑分支，而是 DAG 的一部分**。

---

## 2.10 Agent Lifecycle Management

agent 生命周期由 scheduler 管理。

建议状态：

`created`

刚创建。

`ready`

可接任务。

`running`

正在执行。

`blocked`

被外部条件卡住。

`idle`

暂时无任务但保留。

`recovering`

正在修复问题。

`terminated`

结束。

`archived`

只保留摘要和 memory。

建议回收策略：

短期 agent 在任务完成后可归档。

平台 agent 若后续可能复用，可保持 idle。

长时间 idle 且项目接近结束时归档。

---

## 2.11 Scheduler Persistence

为了支持恢复和断点继续，scheduler 的状态必须持久化。

建议写入：

```
project_x/runtime_state.json
```

包含：

当前 ready 队列

running dispatches

blocked reasons

agent registry snapshot

last scheduling tick

critical path summary

这样系统崩溃后可恢复。

---

# 3. Adapter Plugin System

## 3.1 Design Goal

Adapter Plugin System 的目标是把所有外部 SaaS / CLI / API / MCP / Skill 接入方式，统一成一个可被 agent 调用的插件系统。

这层的价值在于：

上层 agent 不需要理解平台接入细节

新平台可插拔扩展

安全边界可统一控制

调度器只需面向能力标签调度，而不是平台实现细节

---

## 3.2 Plugin Principles

插件系统必须满足：

统一接口

能力声明清晰

认证需求可声明

secret 不暴露给 AI

可发现可注册

可报告错误

可报告状态

支持 CLI/API/MCP/Skill 四类通道

---

## 3.3 Plugin Directory

建议 workspace 中维护：

```
workspace/adapters/
  vercel/
    plugin.yaml
    adapter.py
  supabase/
    plugin.yaml
    adapter.py
  perplexity/
    plugin.yaml
    adapter.py
```

---

## 3.4 Plugin Manifest Schema

每个插件至少有一个 `plugin.yaml`：

```
plugin_id: vercel_adapter
platform: vercel
channel_type: cli
capability_tags:
  - hosting
  - deployment
  - frontend_hosting

auth:
  required: true
  variables:
    - VERCEL_API_TOKEN

actions:
  - authenticate
  - deploy
  - get_status
  - list_projects
  - recover_deployment

requires_user_secret_input: true
ai_secret_visibility: false
```

这个 manifest 是系统发现能力的基础。

---

## 3.5 Unified Adapter Interface

所有 adapter 都要实现统一接口。建议最小接口如下：

```
classAdapterPlugin:
defdiscover_capabilities(self): ...
defvalidate_environment(self): ...
defauthenticate(self,auth_ref): ...
defexecute(self,action,params): ...
defget_status(self,resource_ref): ...
defrecover(self,error_context): ...
```

这里的关键点是：

`authenticate()` 不接收 secret value，而是接收 `auth_ref`。

真正 secret 读取发生在受控 runtime，不进入 AI 上下文。

---

## 3.6 Secret Boundary in Plugin System

你要求 AI 不能接触 API 和敏感数据，所以插件系统必须把 secret handling 从 AI 层彻底隔离。

正确流程应是：

AI 生成变量模板：

```
VERCEL_API_TOKEN=
SUPABASE_API_KEY=
```

用户填写后，secret 写入 workspace vault。

插件收到的是：

```
vault://vercel/token
```

adapter runtime 在受控执行环境中读取 vault。

AI 只知道变量名和 reference，不知道值。

这条边界必须是系统级强约束，而不是提示词约束。

---

## 3.7 Plugin Action Model

每个插件的动作应被标准化。

建议 action 调用统一采用：

```
{
  "action":"deploy",
  "params": {
    "project_path":"artifact://source_code_bundle",
    "config_ref":"memory://resources.md"
  },
  "auth_ref":"vault://vercel/token"
}
```

插件返回：

```
{
  "status":"success",
  "artifacts": [
    {
      "type":"deployment_url",
      "value":"https://..."
    }
  ],
  "logs_ref":"artifact://vercel_logs"
}
```

---

## 3.8 Capability Matching

Scheduler 不应直接说“找 Vercel 插件”，而应先根据任务需要找 capability tag。

例如 task 需要：

```
{
  "agent_type":"hosting_agent",
  "capability_tags": ["hosting","deployment"]
}
```

Adapter registry 会返回所有符合标签的插件：

Vercel

Netlify

Cloudflare Pages

…

再由 Main Agent Council 或 Decision Gate 决定具体平台。

这使得系统更通用。

---

## 3.9 Plugin Lifecycle

插件本身不是 agent，也不是 task。

它是长期存在于 workspace 级别的能力模块。

生命周期通常是：

registered

validated

available

unavailable

deprecated

插件状态影响 scheduler 是否可以派发相关任务。

---

## 3.10 Error Surface

插件必须返回结构化错误，而不是自由文本。

建议格式：

```
{
  "status":"error",
  "error_category":"auth_missing",
  "recoverable":true,
  "message":"Authentication reference missing",
  "suggested_action":"request_user_secret_binding"
}
```

这样 scheduler 和 recovery agent 才能正确处理。

---