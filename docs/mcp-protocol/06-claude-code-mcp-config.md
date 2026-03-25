# Configuring MCP Servers in Claude Code

> Source: https://code.claude.com/docs/en/mcp
> Additional: https://modelcontextprotocol.io/docs/develop/connect-local-servers

This document covers how to configure MCP servers for use with Claude Code (CLI) and Claude Desktop.

---

## Claude Code (CLI) Configuration

### Adding Servers via CLI

#### HTTP Transport (Recommended for Remote)

```bash
# Basic syntax
claude mcp add --transport http <name> <url>

# Example
claude mcp add --transport http notion https://mcp.notion.com/mcp

# With Bearer token
claude mcp add --transport http secure-api https://api.example.com/mcp \
  --header "Authorization: Bearer your-token"
```

#### SSE Transport (Deprecated)

```bash
# Basic syntax
claude mcp add --transport sse <name> <url>

# Example
claude mcp add --transport sse asana https://mcp.asana.com/sse

# With auth header
claude mcp add --transport sse private-api https://api.company.com/sse \
  --header "X-API-Key: your-key-here"
```

#### stdio Transport (Local Servers)

```bash
# Basic syntax
claude mcp add [options] <name> -- <command> [args...]

# Example: Python server
claude mcp add --transport stdio my-server -- python /path/to/server.py

# With environment variables
claude mcp add --transport stdio --env API_KEY=your-key my-server -- python server.py

# Example: npx server
claude mcp add --transport stdio --env AIRTABLE_API_KEY=YOUR_KEY airtable \
  -- npx -y airtable-mcp-server

# Multiple env vars
claude mcp add --transport stdio \
  --env DB_HOST=localhost \
  --env DB_PORT=5432 \
  my-db-server -- python db_server.py
```

**IMPORTANT: Option ordering** - All options (`--transport`, `--env`, `--scope`, `--header`) must come BEFORE the server name. The `--` (double dash) separates the server name from the command and arguments.

### Adding from JSON Configuration

```bash
# HTTP server
claude mcp add-json weather-api '{"type":"http","url":"https://api.weather.com/mcp","headers":{"Authorization":"Bearer token"}}'

# stdio server
claude mcp add-json local-weather '{"type":"stdio","command":"/path/to/weather-cli","args":["--api-key","abc123"],"env":{"CACHE_DIR":"/tmp"}}'

# HTTP server with OAuth
claude mcp add-json my-server '{"type":"http","url":"https://mcp.example.com/mcp","oauth":{"clientId":"your-client-id","callbackPort":8080}}' --client-secret
```

### Managing Servers

```bash
# List all configured servers
claude mcp list

# Get details for a specific server
claude mcp get my-server

# Remove a server
claude mcp remove my-server

# Import from Claude Desktop
claude mcp add-from-claude-desktop

# Reset project-scoped server approval choices
claude mcp reset-project-choices

# Check status (within Claude Code session)
/mcp
```

---

## Configuration File Locations

### Claude Code stores MCP configs in these locations:

| Scope | Location | Purpose |
|-------|----------|---------|
| **Local** (default) | `~/.claude.json` (under project path) | Private to you, current project only |
| **Project** | `.mcp.json` (project root) | Shared via version control, team-wide |
| **User** | `~/.claude.json` (global section) | Available across all projects |
| **Managed** | System-level `managed-mcp.json` | IT-administered, enterprise |

### Scopes

```bash
# Local scope (default) - only you, current project
claude mcp add --transport http stripe https://mcp.stripe.com

# Explicit local scope
claude mcp add --transport http stripe --scope local https://mcp.stripe.com

# Project scope - shared via .mcp.json in version control
claude mcp add --transport http paypal --scope project https://mcp.paypal.com/mcp

# User scope - available across all your projects
claude mcp add --transport http hubspot --scope user https://mcp.hubspot.com/anthropic
```

### Scope Precedence (highest to lowest)

1. **Local** - Personal project-specific
2. **Project** - Shared `.mcp.json`
3. **User** - Cross-project personal

---

## .mcp.json Format (Project-Scoped)

This file goes in your project root and is checked into version control:

```json
{
  "mcpServers": {
    "my-stdio-server": {
      "command": "python",
      "args": ["/path/to/server.py"],
      "env": {
        "API_KEY": "${API_KEY}",
        "DEBUG": "true"
      }
    },
    "my-http-server": {
      "type": "http",
      "url": "https://api.example.com/mcp",
      "headers": {
        "Authorization": "Bearer ${API_TOKEN}"
      }
    },
    "my-sse-server": {
      "type": "sse",
      "url": "http://localhost:3000/sse"
    }
  }
}
```

### Environment Variable Expansion

Supported syntax:
- `${VAR}` - Expands to the value of environment variable `VAR`
- `${VAR:-default}` - Expands to `VAR` if set, otherwise uses `default`

Expansion works in: `command`, `args`, `env`, `url`, `headers`

```json
{
  "mcpServers": {
    "api-server": {
      "type": "http",
      "url": "${API_BASE_URL:-https://api.example.com}/mcp",
      "headers": {
        "Authorization": "Bearer ${API_KEY}"
      }
    }
  }
}
```

If a required env var is not set and has no default, Claude Code will fail to parse the config.

---

## Claude Desktop Configuration

### File Location

| OS | Path |
|----|------|
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux | `~/.config/claude-desktop/claude_desktop_config.json` |

### Format

```json
{
  "mcpServers": {
    "my-server": {
      "command": "python",
      "args": ["/absolute/path/to/server.py"],
      "env": {
        "API_KEY": "your-api-key"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/files"]
    },
    "claude-code-as-mcp": {
      "type": "stdio",
      "command": "claude",
      "args": ["mcp", "serve"],
      "env": {}
    }
  }
}
```

---

## Plugin-Provided MCP Servers

Plugins can bundle MCP servers in `.mcp.json` at the plugin root or inline in `plugin.json`:

```json
{
  "database-tools": {
    "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
    "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
    "env": {
      "DB_URL": "${DB_URL}"
    }
  }
}
```

Or inline in `plugin.json`:

```json
{
  "name": "my-plugin",
  "mcpServers": {
    "plugin-api": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/api-server",
      "args": ["--port", "8080"]
    }
  }
}
```

---

## OAuth Authentication

For servers requiring OAuth 2.0:

```bash
# Add HTTP server
claude mcp add --transport http sentry https://mcp.sentry.dev/mcp

# Then authenticate within Claude Code
/mcp
# Follow browser login flow
```

### Pre-configured OAuth Credentials

```bash
# With client ID and secret
claude mcp add --transport http \
  --client-id your-client-id --client-secret --callback-port 8080 \
  my-server https://mcp.example.com/mcp

# Fixed callback port (for pre-registered redirect URIs)
claude mcp add --transport http \
  --callback-port 8080 \
  my-server https://mcp.example.com/mcp
```

### Override OAuth Metadata Discovery

In `.mcp.json`:

```json
{
  "mcpServers": {
    "my-server": {
      "type": "http",
      "url": "https://mcp.example.com/mcp",
      "oauth": {
        "authServerMetadataUrl": "https://auth.example.com/.well-known/openid-configuration"
      }
    }
  }
}
```

---

## Using Claude Code as an MCP Server

Claude Code can itself serve as an MCP server:

```bash
claude mcp serve
```

Add to Claude Desktop config:

```json
{
  "mcpServers": {
    "claude-code": {
      "type": "stdio",
      "command": "claude",
      "args": ["mcp", "serve"],
      "env": {}
    }
  }
}
```

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `MCP_TIMEOUT` | Server startup timeout in ms (e.g., `MCP_TIMEOUT=10000 claude`) |
| `MAX_MCP_OUTPUT_TOKENS` | Max output tokens per tool call (default: 25000, warning at 10000) |
| `ENABLE_TOOL_SEARCH` | Tool search mode: `auto` (default), `auto:<N>`, `true`, `false` |
| `ENABLE_CLAUDEAI_MCP_SERVERS` | Enable/disable claude.ai MCP servers (`true`/`false`) |

---

## MCP Resources

Reference MCP resources using @ mentions:

```
Can you analyze @github:issue://123 and suggest a fix?
Compare @postgres:schema://users with @docs:file://database/user-model
```

Format: `@server:protocol://resource/path`

---

## MCP Prompts as Commands

MCP prompts appear as slash commands:

```
/mcp__github__list_prs
/mcp__github__pr_review 456
/mcp__jira__create_issue "Bug in login flow" high
```

---

## Dynamic Tool Updates

Claude Code supports MCP `list_changed` notifications. When an MCP server sends a `list_changed` notification, Claude Code automatically refreshes capabilities from that server without reconnecting.

---

## Managed MCP Configuration (Enterprise)

System administrators can deploy managed configs:

| OS | Path |
|----|------|
| macOS | `/Library/Application Support/ClaudeCode/managed-mcp.json` |
| Linux/WSL | `/etc/claude-code/managed-mcp.json` |
| Windows | `C:\Program Files\ClaudeCode\managed-mcp.json` |

Format is the same as `.mcp.json`. When deployed, users cannot add or modify MCP servers.

### Allowlists and Denylists

In managed settings:

```json
{
  "allowedMcpServers": [
    { "serverName": "github" },
    { "serverCommand": ["npx", "-y", "@modelcontextprotocol/server-filesystem"] },
    { "serverUrl": "https://mcp.company.com/*" }
  ],
  "deniedMcpServers": [
    { "serverName": "dangerous-server" },
    { "serverUrl": "https://*.untrusted.com/*" }
  ]
}
```

Denylist takes absolute precedence over allowlist.

---

## Windows Notes

On native Windows (not WSL), local MCP servers using `npx` require the `cmd /c` wrapper:

```bash
claude mcp add --transport stdio my-server -- cmd /c npx -y @some/package
```

Without `cmd /c`, you'll encounter "Connection closed" errors.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Server not connecting | Check `claude mcp list` and `/mcp` status |
| "Connection closed" on Windows | Use `cmd /c` wrapper for npx |
| OAuth redirect fails | Copy callback URL from browser into Claude Code |
| Large output warnings | Set `MAX_MCP_OUTPUT_TOKENS=50000` |
| Slow startup | Set `MCP_TIMEOUT=10000` for longer timeout |
| Server not found | Use absolute paths in `command` field |
