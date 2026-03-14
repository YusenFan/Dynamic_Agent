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
