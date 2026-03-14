## 1. Problem Statement

本系统面向完全不懂技术的用户，解决的问题不是“帮助用户理解技术”，而是“帮助用户完成技术结果”。传统 AI 产品即使能够生成代码、分析需求、提供架构建议，通常仍然停留在认知层或本地生成层，无法真正跨越到外部执行层。用户往往仍需自己理解 hosting、database、deployment、authentication、CLI、API、文档差异与平台选择，最终导致“能生成 demo”但“不能落地上线”。

本项目的目标是构建一个以 Main Agent 为核心编排者的多代理执行系统。用户只需用自然语言表达一个高层目标，例如“我想做一个可以给投资人演示的产品 demo”，系统便能够自动完成需求分析、背景研究、方案构建、代码生成、平台比较、外部系统接入与部署执行，并在关键不可逆节点向用户提供足够信息，让用户做出 informed decision。系统最终交付的成功标准不是代码产物，而是一个真正部署在线上并且可以访问的 web demo。

该系统的根本价值在于，它将非技术用户从具体技术操作中解放出来，使其只承担目标表达与关键决策职责，而将绝大多数分析、执行、接入、恢复与协同过程交给代理系统完成。换言之，本项目不是一个“聊天式软件开发助手”，而是一个“面向结果落地的 AI execution system”。

## 2. Design Goal

本 MVP 的核心目标是验证以下命题：一个以 Main Agent 驱动、按需创建 Subagent、通过统一 adapter interface 连接外部系统、并结合共享记忆与私有记忆的多代理系统，是否能够将用户的一句高层目标转化为一个真实在线、可访问的 web demo。

为了让这个命题可验证，MVP 必须聚焦单一垂直闭环：从自然语言需求到线上 web demo deployment。系统不追求覆盖所有知识工作场景，也不追求一开始支持所有 SaaS、所有工具通道或所有行业任务，而是优先证明“从目标到部署”的可行性与可靠性。

## 3. Core Abstractions

整个系统可以由六个核心抽象构成。

### 3.1 Project

Project 是系统中的顶层任务容器，代表一次完整的用户目标落地过程。它持有该目标的全部结构化状态，包括用户目标、共享记忆、任务图、已产生的产物、决策历史、执行状态与风险状态。Project 是多 agent 协作的统一边界。所有 agent 的工作都围绕 Project 展开，而不是围绕对话消息本身展开。

Project 的本质不是“聊天会话”，而是“任务实体”。这一点非常关键，因为系统需要对项目进行长期追踪、阶段恢复、跨 agent 协同与状态回放。

### 3.2 Main Agent

Main Agent 是整个系统的核心编排者。它不应该是一个全能执行者，而应该是一个严格意义上的 orchestrator。Main Agent 的职责包括：理解用户目标，将目标转化为结构化 brief，生成 task graph，判断是否需要创建 subagent，协调各 subagent 的输出，维护共享记忆，判断何时自动继续执行，何时触发用户决策，以及在出错时启动恢复流程。

Main Agent 不直接承担面向特定平台的深度操作，也不长期维护平台级知识与认证状态。其存在价值在于控制流、任务分解、信息整合、风险判断和交互把关。

Main Agent 不再由单一模型担任，而是由至少三个模型组成一个集体决策单元，用户任务会先经过多个模型讨论，再形成最终结论。

### 3.3 Subagent

Subagent 是围绕某个稳定能力边界而创建的自治执行单元。只有在需要独立权限、独立知识、独立状态，或者某项能力需要长期复用时，系统才会创建 subagent。Subagent 可以是 research agent、build agent、hosting agent、database agent，也可以是与某个外部系统一一对应的 agent，例如 Perplexity agent、Vercel agent、Supabase agent。

每个 Subagent 至少具备以下属性：角色定义、能力绑定、私有记忆、局部状态、可选的认证上下文，以及与 Main Agent 之间的摘要通信机制。Subagent 的意义不在于“更多 agent 更聪明”，而在于职责专门化、权限隔离、状态持久化与知识边界清晰化。

### 3.4 Adapter Interface

系统不应让上层逻辑直接感知 CLI、API、Skill、MCP 的底层差异。所有外部能力源最终都必须被抽象成统一的 adapter interface。对 Main Agent 或 Subagent 来说，外部世界只表现为可发现能力、可建立认证、可执行动作、可读取状态、可返回错误的统一能力接口。

这意味着系统底层可以通过 CLI 接入某个服务，也可以通过 MCP、Skill 或 REST API 接入另一个服务，但在调度层和 agent 逻辑层，访问模式保持一致。这样才能保证架构可扩展，并避免为每种通道单独设计 orchestration 逻辑。

### 3.5 Shared Memory and Private Memory

系统采用双层记忆结构。Shared Memory 是项目级共享记忆，用于存放所有会影响跨 agent 协作的高价值事实；Private Memory 是 agent 私有记忆，用于存放该 agent 的局部经验、局部执行上下文、平台知识与状态积累。

Shared Memory 不是聊天记录，也不是原始对话历史，而是项目的结构化事实层。Private Memory 则不是跨项目通用知识库，而是某一 agent 在某一类能力域或某一平台上的长期工作记忆。二者的区分，是整个多代理系统避免信息污染和上下文过载的关键。

### 3.6 Decision Gate

Decision Gate 是 Main Agent 的核心机制之一，用于决定系统应当继续自动执行，还是应当暂停并请求用户决策。系统默认会自动推进一切低风险、可逆、低成本且高置信度的操作，但在遇到不可逆动作、高影响架构选择、真实外部权限授权、资源创建成本、公开发布行为或系统低置信度情况时，必须进入 Decision Gate。

Decision Gate 的目标不是增加用户操作，而是将复杂技术空间压缩成少量必要、可理解、信息充分的决策节点。

## 4. System Principles

这个系统应遵循以下设计原则。

第一，系统的成功标准是“可访问的在线结果”，不是“高质量建议”，也不是“本地生成代码”。

第二，agent creation 是成本，而不是默认行为，只有满足独立权限、知识、状态或长期复用要求时才创建。

第三，共享记忆只存放跨 agent 协作所需的项目事实，不承载原始低价值上下文。

第四，用户不是系统操作员，而是关键不可逆决策的拥有者。

第五，系统对外部世界的访问必须通过统一 adapter interface 完成。

第六，系统应默认自动推进，只有在 Decision Gate 条件成立时才暂停请求用户。

第七，错误处理必须被显式建模，而不是作为临时异常分支存在。

第八，长期 agent 的知识更新应以“相关、最新、可验证”为原则，而不是无限累积网页内容。

## 5. Agent Lifecycle

Agent 生命周期需要被设计成清晰、可控、可恢复的状态机，而不是松散的“需要时生成，用完即忘”。

### 5.1 Creation Rule

只有当某项任务满足以下任一条件时，系统才应创建 Subagent：该任务需要独立权限边界，例如登录某个外部平台；该任务需要长期维护的知识域，例如研究、托管平台文档、数据库文档；该任务需要独立状态，例如保留 CLI 环境、认证状态、平台 session；该能力未来很可能被反复调用，具有持续存在的价值。

如果某项任务只是一次性简单调用，不需要专属记忆、不需要持续权限、不需要多轮交互，则不创建 Subagent，而由 Main Agent 直接通过 adapter 执行即可。

### 5.2 Lifecycle States

每个 agent 可以具有如下生命周期状态：initialized、active、waiting、suspended、recovering、terminated、archived。

initialized 表示 agent 已创建但尚未开始执行。active 表示 agent 正在执行其能力域内的任务。waiting 表示 agent 当前无待执行任务，但仍保留上下文和状态。suspended 表示 agent 被暂时挂起，例如等待用户决策或等待外部依赖。recovering 表示 agent 正在参与错误恢复流程。terminated 表示 agent 生命周期已结束，不再参与当前项目。archived 表示 agent 被回收，但其关键摘要、状态和私有经验片段被保留，以支持后续恢复或相似任务复用。

### 5.3 Agent Categories

在 MVP 中，可以将 agent 分为三类。第一类是 persistent domain agent，例如 Perplexity research agent、Vercel agent、Supabase agent。这类 agent 的价值在于长期状态和平台知识积累。第二类是 episodic execution agent，例如某次 UI scaffold agent 或某次 bug fix agent，它们围绕特定阶段任务存在，任务结束后即回收。第三类是 recovery agent，它们由 Main Agent 在错误发生后生成，专门负责某类错误的修复和恢复。

### 5.4 Lifecycle Ownership

Main Agent 负责 agent 的创建、暂停、恢复、终止和回收决策。Subagent 不应自行无限扩张创建新的 agent，除非系统未来明确支持 delegation cascade。在 MVP 中，为控制复杂性，建议只有 Main Agent 拥有 spawn 权限，Subagent 只能请求 Main Agent 创建新的代理，而不能直接创建。

## 6. Memory Schema

Memory 设计是本系统的核心基础设施。MVP 中采用项目级共享记忆与 agent 私有记忆并存的结构。

### 6.1 Shared Memory

Shared Memory 是项目的结构化事实层，采用以下六个主槽位：

Goals：记录用户目标与系统当前阶段性目标。例如“构建一个可给投资人演示的 web demo 并成功部署上线”。

Constraints：记录约束条件，例如用户不懂技术、优先低门槛部署、预算敏感、希望尽量少交互。

Decisions：记录用户已确认或系统已锁定的关键决策，例如选择 Vercel 作为 hosting、选择 Supabase 作为 database。

Resources：记录项目已接入和可用的资源，例如 GitHub repository、Vercel account status、Perplexity API access、可调用 adapter。

Progress：记录当前任务阶段、已完成里程碑、待办节点、阻塞状态。

Risks：记录当前存在的主要不确定性与风险，例如尚未完成授权、平台限制未知、部署路径未最终确认。

Shared Memory 中不应存储大段原始对话，不应存储低价值搜索噪音，也不应存储 agent 内部细粒度试错过程。写入 shared memory 的内容必须是对项目事实具有长期价值、对跨 agent 协作具有直接作用的结构化信息。

### 6.2 Private Memory

Private Memory 属于单个 agent，用于保存其局部能力域内的长期和中期状态。对于 research agent，这可能包括查询策略、来源偏好、已验证背景结论。对于 Vercel agent，这可能包括认证状态、CLI 行为、部署经验、平台常见故障模式。对于 database agent，这可能包括连接配置模式、schema 建议、常见限制与修复经验。

Private Memory 的作用有两个。第一，减少每次执行都重新加载同一类平台知识的成本。第二，使 agent 具有“持续专业化”的特征，而不是每次从零开始。

### 6.3 Session Scratchpad

除 Shared Memory 和 Private Memory 外，系统在运行时还应存在短期推理用的 scratchpad，但这类内容不应默认长期保存。Scratchpad 主要承载某次执行中的中间思路、临时命令、局部推理缓存。它的保存门槛应高于普通运行缓存，只有在其结果对未来具有恢复价值或经验价值时，才被压缩写入 private memory 或 shared memory。

### 6.4 Write Policy

Main Agent 对 shared memory 拥有最高写入权限。Subagent 仅可在其输出经过摘要、结构化、去噪后，由 Main Agent 写入共享记忆，或者在严格授权下直接写入某些特定槽位。Private Memory 只由对应 agent 维护，不对其他 agent 直接开放原始访问，其他 agent 如有需要，应通过 Main Agent 请求摘要。

这种写入策略可以有效避免共享记忆膨胀、事实冲突和跨 agent 污染。

## 7. Task Flow

MVP 的标准任务流从用户的一句高层目标开始，到线上可访问 demo 结束。

### 7.1 User Goal Intake

用户通过自然语言输入目标，例如“我想做一个可以上线给别人访问的 demo”。Main Agent 对输入进行初步解析，识别目标类型、预期结果、潜在用户群、产品形态、是否涉及数据保存、是否涉及登录、是否涉及公开访问等信息。

### 7.2 Brief Structuring

Main Agent 将自然语言需求转化为结构化 project brief，并初始化 shared memory。此时 Goals、Constraints 和初始 Risks 会被写入系统。若输入中存在高价值但尚未明确的信息缺口，Main Agent 不应立即提出大量技术问题，而应优先通过合理假设和 research 来缩小不确定性空间。

### 7.3 Task Graph Generation

Main Agent 根据 brief 生成任务图。对于 web demo deployment 场景，典型任务包括产品背景研究、需求补全、信息架构、技术方案选择、代码 scaffold、页面生成、部署方案比较、平台接入、部署执行、验收检查。

### 7.4 Subagent Spawning

Main Agent 根据任务图判断是否需要创建 subagent。例如 research task 可触发 Perplexity agent；代码搭建可触发 build agent；当用户选择某一 hosting platform 时，可创建对应 hosting agent；当需要持久化数据时，可创建 database agent。

### 7.5 Autonomous Work Phase

各 subagent 在各自能力边界内执行工作，并将高价值结论以摘要形式返回给 Main Agent。Main Agent 不需要接收所有细粒度中间过程，只需要接收足够维持控制流和项目事实更新的结果。

### 7.6 Decision Gate Entry

当系统进入高影响节点，例如选择 hosting、选择 database、授权真实账户、创建公开资源、绑定域名、触发潜在付费行为时，Main Agent 进入 Decision Gate。此时系统要向用户提供充分信息，包括候选选项、适用场景、优点、缺点、成本、风险、推荐理由和切换代价。用户据此做出选择。

### 7.7 Execution and Deployment

用户确认后，相关 subagent 通过 adapter interface 调用对应 CLI、API、Skill 或 MCP，与外部系统交互，完成实际资源接入与部署执行。执行过程中，Main Agent 追踪状态变更、更新 shared memory，并在必要时触发恢复流程。

### 7.8 Verification and Delivery

部署完成后，系统执行验收流程，包括链接可访问性检查、部署状态确认、关键页面加载检查、必要时的基础功能 smoke test。通过验证后，系统将在线可访问结果作为最终交付物呈现给用户，同时记录最终 Decisions、Resources、Progress 与残余 Risks。

## 8. Error Recovery Model

虽然本次文档不要求展开完整 recovery architecture，但 MVP 仍需明确其基本逻辑。所有错误先由 Main Agent 统一接收和分类，再决定下一步处理方式。若错误属于可自动恢复范畴，例如命令格式问题、环境配置问题、依赖缺失、文档策略错误，则 Main Agent 生成对应 recovery agent 处理。若错误涉及用户账户授权、付费限制、公开风险、资源策略分歧或系统低置信度，则错误将转化为新的 Decision Gate 节点，由用户决定。

恢复过程结束后，应将错误类型、采取动作、处理结果与可复用经验回写到相应记忆层中，以提高系统后续项目中的稳定性。

## 9. MVP Scope

本 MVP 的范围必须严格受控，以证明核心命题，而不是追求功能广度。

MVP 支持的用户类型是完全不懂技术、但希望快速获得线上 demo 的用户。

MVP 支持的目标类型是 web demo deployment。

MVP 的成功标准是将一句自然语言目标转化为一个线上可访问的 demo。

MVP 的核心系统能力包括 Main Agent orchestration、按需生成 Subagent、统一 adapter interface、共享与私有记忆、Decision Gate、基础错误恢复流程。

MVP 可支持少量高价值外部系统，例如一个 research provider、一个 code repository provider、一个 hosting provider、一个 database provider。

MVP 的重点不是最大化平台支持数量，而是证明单条任务链路能够真实闭环。

从产品层面，MVP 的用户体验目标是：用户尽可能少输入、尽可能少做技术判断、只在关键不可逆节点做选择，并且每次选择前都获得足够信息。

## 10. v1 Non-Goals

为了防止范围失控，以下内容应明确排除在 v1 之外。

v1 不追求成为通用型全场景多 agent 平台，不覆盖 sales、marketing、finance、operations 等所有知识工作流。

v1 不支持任意数量的第三方平台与任意通道接入，不要求一次性兼容所有 CLI、Skill、MCP 生态。

v1 不追求完全自动化而零用户确认，凡涉及不可逆、外部授权、成本与公开暴露面的操作仍必须由用户决策。

v1 不构建复杂的长期自主学习系统，不做无边界的 agent 自我进化机制。

v1 不做全量 multi-agent delegation tree，不允许 subagent 任意继续 spawn subagent。

v1 不做复杂团队协作、多用户项目管理、角色权限系统。

v1 不支持生产级别的大规模 observability、审计、策略引擎和企业安全治理。

v1 不将 shared memory 设计成全量对话数据库，也不构建复杂的通用知识图谱。

v1 不承诺生成生产级 SaaS 产品，只承诺生成可访问、可演示、可验证的 web demo。