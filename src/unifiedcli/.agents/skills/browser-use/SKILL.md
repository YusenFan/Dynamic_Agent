---
name: browser-use
description: Browse the web to find information, documentation, tutorials, and solutions. Use when an agent needs to research external platforms, read API docs, find deployment guides, troubleshoot errors by searching, or gather any information not available locally. This skill should be used whenever the agent encounters unknown territory — unfamiliar platforms, undocumented behavior, new tools, or error messages it hasn't seen before.
---

# Browser Use

This skill enables agents to browse the web for information gathering, research, and problem-solving.

## When to Use This Skill

Use this skill when you need to:

- Research a platform, tool, or service you don't have prior knowledge about
- Read official documentation for APIs, CLIs, or SDKs
- Find tutorials or guides for specific deployment scenarios
- Search for error messages or troubleshooting steps
- Gather information about pricing, features, or limitations of external services
- Verify that URLs, endpoints, or resources are accessible
- Find code examples or implementation patterns

## How to Use

### Web Search

Search for information using targeted queries:

```
Search: "Vercel CLI deploy Next.js project"
Search: "Supabase create table REST API"
Search: "error ENOENT package.json deploy"
```

**Tips for effective searches:**
- Be specific: include platform name, action, and technology
- Include error codes or exact error messages when troubleshooting
- Add "official docs" or "documentation" to find authoritative sources
- Use quotes around exact phrases

### Web Fetch

Fetch and read specific web pages:

```
Fetch: https://vercel.com/docs/cli
Fetch: https://supabase.com/docs/reference/javascript/introduction
```

**Tips for fetching:**
- Prefer official documentation URLs over blog posts
- API reference pages are more reliable than tutorials for exact syntax
- Check the page date — prefer recent content

## Information Extraction

When browsing, extract and structure the relevant information:

1. **Key facts** — Configuration values, API endpoints, required parameters
2. **Step-by-step procedures** — Installation, setup, deployment sequences
3. **Constraints and limitations** — Rate limits, size limits, platform restrictions
4. **Error patterns** — Common failure modes and their fixes

## Output Format

After browsing, summarize findings as structured facts that can be written to agent memory:

```markdown
## Research: [Topic]

### Key Findings
- Finding 1
- Finding 2

### Action Items
- What needs to happen based on this research

### Sources
- URL 1 (what it contained)
- URL 2 (what it contained)
```

## Integration with Other Skills

- If research reveals a need for a specialized tool → use **find-skills** to check if a skill exists
- If no skill exists and one would be valuable → use **skill-creator** to build one
- Always write key findings to agent private memory for future reference
