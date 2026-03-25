# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OSCAR is a build package for creating a secure MCP (Model Context Protocol) server that gives Claude Code full control over Autodesk Fusion 360. It replaces insecure third-party MCPs with a clean, minimal, localhost-only alternative.

This repo is primarily **documentation and specifications** — not a running codebase. There are no build/test/lint commands. The output of following these docs is a two-process system built by Claude Code.

## How to Use This Package

1. Read `docs/aurafriday-analysis/WHY-DISCONNECT.md` — understand and remove any insecure MCP
2. Feed `prompt/MASTER-PROMPT.md` to Claude Code — this is the complete build prompt
3. Reference `build-guide/BUILD-GUIDE.md` for the full architecture spec and implementation details
4. Reference `docs/` and `fusion-api/` for API details as needed during implementation

## Architecture (What Gets Built)

A **two-process system** bridged by HTTP on localhost:

```
Claude Code ──stdio──> MCP Server (FastMCP, system Python, port configurable)
                              │
                         HTTP POST (127.0.0.1:45876)
                         Bearer token auth
                              │
                              ▼
                       Fusion Add-in (runs inside Fusion 360's process)
                         └── CustomEvent handler on main thread
```

### Process 1: Fusion Add-in (`fusion_bridge`)
- Runs INSIDE Fusion 360's bundled Python interpreter
- **Stdlib only** — no pip, no external packages
- HTTP server on a background daemon thread, bound to `127.0.0.1`
- Uses Fusion's CustomEvent system to marshal API calls to the main thread (the ONLY safe threading pattern)
- Generates a random Bearer auth token on startup, shown in Fusion's TEXT COMMANDS panel

### Process 2: MCP Server (`fusion_mcp_server`)
- Separate Python process using FastMCP with stdio transport
- Runs in system Python (can use pip packages: `pip install mcp`)
- Receives tool calls from Claude, forwards as HTTP requests to the Fusion add-in

## Critical Fusion 360 API Constraints

- **`Application.fireCustomEvent()` is the ONLY Fusion API call safe from background threads.** All other API calls must happen on the main thread via the CustomEvent handler pattern.
- The add-in must be structured as an **add-in** (not a script) — add-ins persist across sessions and can run background threads.
- **Only use API information from the docs in this package** (`fusion-api/` and `docs/fusion-api/`). Do not rely on training data for Fusion API — methods may be retired, renamed, or behave differently than expected.

## Key Documentation

| Path | Purpose |
|------|---------|
| `prompt/MASTER-PROMPT.md` | Complete build prompt — feed this to Claude Code |
| `build-guide/BUILD-GUIDE.md` | Full architecture spec with working code patterns |
| `fusion-api/00-INDEX.md` | Index of 25 Fusion API reference files with reading order |
| `docs/mcp-protocol/00-INDEX.md` | Index of 7 MCP protocol reference files |
| `docs/aurafriday-analysis/WHY-DISCONNECT.md` | Security analysis of the old MCP + removal steps |

## Security Requirements (Non-Negotiable)

- Localhost-only binding (`127.0.0.1`, never `0.0.0.0`)
- Random auth token generated on each startup
- No opaque binaries, no auto-updater, no bundled bloat
- No external dependencies in the Fusion add-in (stdlib only)

## Fusion Design Session — Best Practices

These best practices apply to Fusion modeling sessions.

### Startup Checklist
1. **Read `docs/FUSION-BEST-PRACTICES.md`** — the complete 72-rule modeling guide. Do this FIRST, every session.
2. `fusion_ping` — verify the bridge is alive
3. New document → **immediately** set `design.designType = ParametricDesignType` and verify `== 1`. New docs default to direct mode (no timeline).
4. **Name the document** something meaningful right after creation (e.g., "Storage Box", "Motor Mount"). Never leave it as "Untitled".
5. `fusion_pin` — pin the document before any geometry work. Keep it pinned for the entire modeling session. Only `fusion_unpin` when the user says to move on to a different project.

### The Parameter Prime Directive
**Every dimension must be a named user parameter.** Never hardcode a number into a sketch or feature. Create all parameters up front before geometry, with descriptive names and comments. This is non-negotiable.

### Modeling Best Practices
- **Name every body** with an intuitive name immediately after creation
- **Always use parametric mode** — the user must see a timeline
- **Verify sketches are not construction lines** before using as profiles
- **Check and manage body visibility** before all cut/boolean operations — hidden bodies are silently skipped
- **Pick sketch profiles by area** — `item(0)` is often the outer region, not what you want
- **Never use `setAllExtent`** on hollow bodies — use `setDistanceExtent` instead
- **Signal progress** to the user ("working..." / "done") and re-verify active component in every code block
- **Use `fusion_capture`** to visually verify geometry before telling the user "done"
- **Ask clarifying questions** with selectable options before starting ambiguous modeling tasks
- **Run engineering/physics calcs BEFORE modeling**, verify with Fusion's CG tool after

### Experience Files
As you use OSCAR, save your learnings in the `experience/` folder. See `experience/README.md` for the format. These accumulate into expertise that makes OSCAR dramatically more effective over time.

**Before saving an experience file, always ask the user:**
> "Should this go in `experience/` (public — will be committed and shared) or `experience/private/` (local only — gitignored, stays on your machine)?"

- `experience/` — public learnings intended to help the community. These get committed to the repo.
- `experience/private/` — personal notes, project-specific quirks, or anything you'd rather not share. This directory is gitignored.

## Prerequisites for Building

- Autodesk Fusion 360 installed
- Python 3.10+ (system Python, separate from Fusion's bundled Python)
- `pip install mcp` (for the MCP server component)
