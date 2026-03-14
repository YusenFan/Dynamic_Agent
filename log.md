# Change Log

## 2026-03-13 — Core Engine Implementation (All 5 Phases)

### Phase 1: Foundation — Models + Memory + Graph
- Created all Pydantic data models in `src/unifiedcli/models/` (task, agent, project, workspace, adapter, decision, memory, council)
- Implemented `SharedMemoryManager` — 6 markdown slot files (goals, constraints, decisions, resources, progress, risks)
- Implemented `PrivateMemoryManager` — per-agent memory (knowledge, execution_patterns, failures, sessions)
- Implemented `Scratchpad` — ephemeral key-value store with optional file persistence
- Implemented `TaskGraphEngine` — DAG with add/remove nodes+edges, state transitions, `get_ready_tasks()`, runtime expansion, retry
- Implemented cycle detection via Kahn's algorithm topological sort
- Implemented JSON serialization/deserialization for task_graph.json

### Phase 2: Infrastructure — Adapters + Vault + Workspace
- Implemented `VaultManager` — store/resolve/delete vault:// references, AI never sees secret values
- Implemented `AdapterPlugin` ABC — unified interface (discover, validate, authenticate, execute, get_status, recover)
- Implemented `loader.py` — load plugin.yaml manifests from disk
- Implemented `AdapterRegistry` — register plugins, match by capability tags, track lifecycle status
- Implemented `WorkspaceManager` — workspace init, config, project CRUD, adapter registry, vault access
- Implemented `ProjectManager` — project config (YAML), scoped memory/graph/agents access
- Implemented workspace/project directory bootstrapping

### Phase 3: Agent Runtime + Decisions
- Implemented `BaseAgent` ABC — execute_task, on_blocked, on_terminate
- Implemented `AgentLifecycleManager` — create, find matching, transition, terminate, archive agents
- Implemented decision trigger evaluators (irreversible, cost, auth, lock-in, public, low confidence)
- Implemented `DecisionGateEngine` — build decision packets, CLI user prompts

### Phase 4: Council + Scheduler
- Implemented LLM provider abstraction (Claude, OpenAI, Gemini providers + MockLLMProvider)
- Implemented 5-step deliberation protocol: plan → critique → respond → balance → update memory
- Implemented `Council` orchestrator with `deliberate()`, `plan_task_graph()`, `evaluate_failure()`
- Implemented task priority ranking (critical-path aware, recovery/verify/decision boosted)
- Implemented agent matching (reuse > spawn > direct execution)
- Implemented core scheduler loop: scan → rank → match → dispatch → collect → update

### Phase 5: Main Agent + CLI
- Implemented `MainAgent` with full state machine (IDLE→INTAKE→PLANNING→ALLOCATING→EXECUTING→WAITING_FOR_USER_DECISION→RECOVERY_COORDINATION→VERIFYING→TERMINAL)
- Implemented CLI entry point with commands: init, new, status, resume, list

### Tests
- 48 tests across all modules, all passing
- Covers: graph engine, serialization, shared/private memory, scratchpad, vault, registry, triggers, priority, matching, scheduler, council, workspace, project

## 2026-03-14 — Skill System + Dynamic Agent Skill Installation

### Skill System
- Created `SkillManager` (`src/unifiedcli/agents/skills.py`) — scans skills directory, parses SKILL.md frontmatter, matches skills to tasks
- 3 basic skills always installed for ALL agents (main agent + subagents):
  - `find-skills` — discover and install skills from the ecosystem
  - `browser-use` — browse the web for research/docs/troubleshooting (NEW)
  - `skill-creator` — create new skills when no existing skill fits
- Created `browser-use` skill (`src/unifiedcli/.agents/skills/browser-use/SKILL.md`)

### Agent Spawn Improvements
- `spawn_reason` now descriptive: includes task name, type, description, capability tags, expected outputs (was just "Spawned for task {task_id}")
- Added `installed_skills` field to `AgentSpec` model
- Scheduler auto-installs basic skills + matched skills on agent creation via `SkillManager.install_for_agent()`
- Skill matching uses task description + spawn reason + capability tags to find relevant skills
- Backward compatible — scheduler works without SkillManager

### Skill Lifecycle on Spawn
1. Agent spawned with descriptive `spawn_reason` from task context
2. `SkillManager.install_for_agent()` loads 3 basic skills + matches additional skills
3. If no relevant skill found at spawn, agent can use `find-skills` at runtime to discover one
4. If nothing exists in the ecosystem, agent can use `browser-use` to research, then `skill-creator` to build one

### Tests
- 62 total tests (was 48+2, now +12 new), all passing
- New tests: SkillManager scanning, SKILL.md parsing, spawn_reason builder, full integration (spawn with skills installed), backward compat (spawn without SkillManager)

### CLI — API Key Configuration + Real Council Execution
- `unifiedcli init` now prompts for 3 API keys (Claude, Gemini, OpenAI) and stores them in vault
- `unifiedcli new` builds a real Council (Claude=Planner, Gemini=Critic, OpenAI=Balancer) and runs the full MainAgent lifecycle: intake → plan → execute → verify
- `unifiedcli resume` loads keys from vault and resumes execution with real Council
- `unifiedcli configure` added — update API keys at any time
- `unifiedcli status` shows API key configuration status
- Keys stored securely via VaultManager (vault://claude/api_key, vault://gemini/api_key, vault://openai/api_key) — AI never sees raw values
