# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

UnifiedCLI is a multi-agent AI execution system that converts natural language goals from non-technical users into deployed, accessible web demos. It is NOT a chatbot or code assistant — it is an execution system focused on real deployment outcomes.

The system design document is in `systemdesign.md` (written in Chinese). High level technical structure is in `technicalspecv1.md` (written in Chinese). The core engine layer is in `coreComponentSpec.md`. Key files: `log.md` is for record all changes that maded by ClaudeCode.

## Architecture (from system design)

Six core abstractions:

1. **Project** — Top-level task container (not a chat session). Holds goals, shared memory, task graph, artifacts, decisions, execution state, and risks.
2. **Main Agent** — Central orchestrator. Does NOT execute platform-specific work directly. Responsibilities: goal parsing → structured brief → task graph → subagent coordination → shared memory maintenance → decision gates → error recovery.
3. **Subagent** — Autonomous execution units created on-demand (not by default). Types: persistent domain agents (e.g., Vercel, Supabase, Perplexity), episodic execution agents (e.g., UI scaffold), recovery agents. Only Main Agent can spawn subagents.
4. **Adapter Interface** — Unified abstraction over CLI/API/Skill/MCP. Agents never interact with external systems directly — always through adapters.
5. **Memory** — Dual-layer: Shared Memory (project-level structured facts in 6 slots: Goals, Constraints, Decisions, Resources, Progress, Risks) and Private Memory (per-agent domain knowledge). Session Scratchpad exists for ephemeral reasoning.
6. **Decision Gate** — Pauses automation for user input at irreversible/high-impact points (hosting choice, auth, payments, public exposure).

## Key Design Principles

- Success = live, accessible web demo (not code generation or advice)
- Subagent creation is a cost — only create when independent auth/knowledge/state/reuse is needed
- Shared memory stores only cross-agent project facts, never raw conversation
- Users make decisions only at critical irreversible points
- All external access goes through unified adapter interface
- Default to autonomous execution; pause only at Decision Gates
- Errors are explicitly modeled, not ad-hoc exception handling

## MVP Scope

- Single vertical: natural language goal → deployed web demo
- Target users: completely non-technical
- Few external integrations: one each for research, code repo, hosting, database
- No multi-user, no enterprise features, no production SaaS output
- Subagents cannot spawn other subagents

## Task Flow

User goal → Brief structuring → Task graph generation → Subagent spawning → Autonomous work → Decision gates → Execution/deployment → Verification/delivery
