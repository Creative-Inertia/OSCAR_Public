# OSCAR — Open Source CAD Automation Rig

A secure MCP (Model Context Protocol) server that gives Claude Code full control over Autodesk Fusion 360.

## What Is This?

OSCAR is a build package that creates a two-process bridge between Claude Code and Fusion 360. Feed the master prompt to Claude Code, and it builds the entire system for you — a Fusion add-in and an MCP server that lets Claude design, model, and manipulate 3D geometry through natural conversation.

```
Claude Code ──stdio──> MCP Server (FastMCP, Python)
                              │
                         HTTP POST (localhost:45876)
                         Bearer token auth
                              │
                              ▼
                       Fusion Add-in (runs inside Fusion 360)
```

## Quick Start

1. **Read** `docs/aurafriday-analysis/WHY-DISCONNECT.md` if you have the AuraFriday MCP installed
2. **Feed** `prompt/MASTER-PROMPT.md` to Claude Code
3. **Reference** `build-guide/BUILD-GUIDE.md` for the full architecture spec
4. **Install and test** — follow the steps in the build guide

```bash
# Option 1: Feed the master prompt directly
claude "$(cat prompt/MASTER-PROMPT.md)"

# Option 2: Paste the contents of prompt/MASTER-PROMPT.md into a Claude Code session
```

## Prerequisites

- Autodesk Fusion 360 installed
- Python 3.10+ (system Python, separate from Fusion's bundled Python)
- `pip install mcp` (for the MCP server component)
- Claude Code (claude.ai/code)

## What's Inside

```
OSCAR/
├── prompt/MASTER-PROMPT.md           # Feed this to Claude Code to build the system
├── build-guide/BUILD-GUIDE.md        # Full architecture spec + implementation details
├── docs/
│   ├── aurafriday-analysis/          # Security analysis of the old MCP
│   ├── fusion-api/                   # 17 Fusion 360 API reference files
│   ├── mcp-protocol/                 # 7 MCP protocol reference files
│   ├── FUSION-BEST-PRACTICES.md      # 72-rule modeling guide
│   └── TESTING-GUIDE.md              # Testing instructions
├── fusion-api/                       # 36 extended API reference files
├── fusion_bridge/                    # Fusion add-in source code
├── fusion_mcp_server/                # MCP server source code
└── experience/                       # Your learnings go here (see below)
```

## The Experience Layer

As you use OSCAR, you'll discover API quirks, develop modeling recipes, and learn what works. These hard-won lessons — your **experience** — make OSCAR dramatically better over time.

The `experience/` folder is where you store these learnings. They're yours to keep private or share.

### Sharing Your Experience

We'd love to build a shared knowledge base. If you've discovered something useful, submit a PR with your experience files. Over time, the community's collective expertise will make OSCAR smarter for everyone.

See `experience/README.md` for the format.

## Security

- **Localhost-only** — binds to `127.0.0.1`, never `0.0.0.0`
- **Token auth** — random Bearer token generated on each startup
- **No binaries** — you own every line of code
- **No auto-updater** — no phone-home, no bundled bloat
- **Stdlib only** in the Fusion add-in — no pip dependencies inside Fusion

## Architecture

The system uses two processes bridged by HTTP:

**Fusion Add-in** (`fusion_bridge/`) — runs inside Fusion 360's Python interpreter. Uses Fusion's CustomEvent system to safely marshal API calls from a background HTTP server thread to the main thread.

**MCP Server** (`fusion_mcp_server/`) — runs as a separate Python process using FastMCP with stdio transport. Receives tool calls from Claude Code and forwards them as HTTP requests to the add-in.

## License

MIT
