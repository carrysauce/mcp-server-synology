# 💾 Synology MCP Server

![Synology MCP Server](assets/banner.png)

A Model Context Protocol (MCP) server for Synology NAS devices. It exposes Synology FileStation, Download Station, health, NFS, and user-management operations as MCP tools.

## Highlights

- `TRANSPORT=stdio` for local MCP clients like Claude Desktop and Cursor
- `TRANSPORT=http` for remote deployments behind a reverse proxy
- Official MCP streamable HTTP transport at `HTTP_PATH` (default `/mcp`)
- Optional shared-secret gate with `HTTP_QUERY_TOKEN`
- Existing MCP tools preserved unchanged

> `mcp` now requires `>=1.27.0` so streamable HTTP is available out of the box.

## Quick start

### 1. Clone and configure

```bash
git clone https://github.com/carrysauce/mcp-server-synology.git
cd mcp-server-synology
cp env.example .env
```

Set your Synology connection details in `.env` or use `~/.config/synology-mcp/settings.json`.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run in stdio mode

```bash
TRANSPORT=stdio python main.py
```

### 4. Run in HTTP mode

```bash
TRANSPORT=http \
HTTP_HOST=0.0.0.0 \
HTTP_PORT=8765 \
HTTP_PATH=/mcp \
python main.py
```

If you want a simple shared secret in front of the HTTP endpoint:

```bash
TRANSPORT=http \
HTTP_QUERY_TOKEN=replace-me \
python main.py
```

Requests must then include `?token=replace-me`.

## Docker

### Docker Compose

```bash
docker-compose up -d --build
```

The compose file passes through:

- `TRANSPORT` (`stdio` by default)
- `HTTP_HOST`
- `HTTP_PORT`
- `HTTP_PATH`
- `HTTP_QUERY_TOKEN`

It also publishes `${HTTP_PORT:-8765}` for HTTP mode.

### Example HTTP deployment

```bash
TRANSPORT=http HTTP_PORT=8765 docker-compose up -d --build
```

Then point your reverse proxy at `http://<container-host>:8765/mcp`.

## Client setup

### Claude Desktop

```json
{
  "mcpServers": {
    "synology": {
      "command": "python",
      "args": ["main.py"],
      "cwd": "/path/to/mcp-server-synology",
      "env": {
        "TRANSPORT": "stdio",
        "SYNOLOGY_URL": "http://192.168.1.100:5000",
        "SYNOLOGY_USERNAME": "your_username",
        "SYNOLOGY_PASSWORD": "your_password"
      }
    }
  }
}
```

### Cursor

```json
{
  "mcpServers": {
    "synology": {
      "command": "python",
      "args": ["main.py"],
      "cwd": "/path/to/mcp-server-synology",
      "env": {
        "TRANSPORT": "stdio"
      }
    }
  }
}
```

### Remote HTTP clients

Use the streamable HTTP endpoint:

```text
https://your-domain.example/mcp
```

If `HTTP_QUERY_TOKEN` is set, append:

```text
https://your-domain.example/mcp?token=your_shared_secret
```

## Configuration

> **Security warning:** create a dedicated Synology user with only the permissions this MCP server needs. Avoid using your primary admin account, especially if it has 2FA enabled.

### Environment variables

| Variable | Required | Default | Description |
|---|---|---:|---|
| `SYNOLOGY_URL` | Yes* | - | NAS base URL such as `http://192.168.1.100:5000` |
| `SYNOLOGY_USERNAME` | Yes* | - | Synology username |
| `SYNOLOGY_PASSWORD` | Yes* | - | Synology password |
| `AUTO_LOGIN` | No | `true` | Auto-login on server start |
| `VERIFY_SSL` | No | `false` | Verify NAS SSL certificates |
| `DEBUG` | No | `false` | Enable debug logging |
| `LOG_LEVEL` | No | `INFO` | Log level |
| `TRANSPORT` | No | `stdio` | MCP transport: `stdio` or `http` |
| `HTTP_HOST` | No | `0.0.0.0` | HTTP bind host when `TRANSPORT=http` |
| `HTTP_PORT` | No | `8765` | HTTP listen port when `TRANSPORT=http` |
| `HTTP_PATH` | No | `/mcp` | Streamable HTTP route when `TRANSPORT=http` |
| `HTTP_QUERY_TOKEN` | No | - | Optional `?token=` secret required for HTTP requests |

\* Required for auto-login and default operations if not provided in `settings.json`.

### settings.json (recommended for credentials)

The server follows the XDG base directory layout and reads:

```text
~/.config/synology-mcp/settings.json
```

Create it with secure permissions:

```bash
mkdir -p ~/.config/synology-mcp
touch ~/.config/synology-mcp/settings.json
chmod 600 ~/.config/synology-mcp/settings.json
```

Example:

```json
{
  "synology": {
    "nas1": {
      "host": "192.168.1.100",
      "port": 5000,
      "username": "admin",
      "password": "your_password",
      "note": "Primary NAS"
    },
    "nas2": {
      "host": "192.168.1.200",
      "port": 5001,
      "username": "admin",
      "password": "your_password",
      "note": "Backup NAS"
    }
  },
  "server": {
    "auto_login": true,
    "verify_ssl": false,
    "session_timeout": 3600,
    "debug": false,
    "log_level": "INFO"
  }
}
```

Notes:

- Port `5001` is treated as HTTPS; other ports default to HTTP.
- `settings.json` takes priority for Synology credentials.
- The server refuses to load `settings.json` if permissions are too open.

## Available MCP tools

### Authentication

- `synology_status`
- `synology_list_nas`
- `synology_login`
- `synology_logout`

### FileStation

- `list_shares`
- `list_directory`
- `get_file_info`
- `search_files`
- `create_file`
- `create_directory`
- `delete`
- `rename_file`
- `move_file`

### Download Station

- `ds_get_info`
- `ds_list_tasks`
- `ds_create_task`
- `ds_pause_tasks`
- `ds_resume_tasks`
- `ds_delete_tasks`
- `ds_get_statistics`

### Health

- `synology_system_info`
- `synology_utilization`
- `synology_disk_health`
- `synology_disk_smart`
- `synology_volume_status`
- `synology_storage_pool`
- `synology_network`
- `synology_ups`
- `synology_services`
- `synology_system_log`
- `synology_health_summary`

### NFS

- `synology_nfs_status`
- `synology_nfs_enable`
- `synology_nfs_list_shares`
- `synology_nfs_set_permission`

### User management

- `synology_list_users`
- `synology_get_user`
- `synology_create_user`
- `synology_delete_user`
- `synology_set_user_password`
- `synology_enable_user`
- `synology_disable_user`
- `synology_list_groups`
- `synology_create_group`
- `synology_delete_group`
- `synology_add_user_to_group`
- `synology_remove_user_from_group`
- `synology_get_user_permissions`
- `synology_set_user_permissions`

## Security recommendations

### SSL verification

- `VERIFY_SSL=false` is the default for self-signed NAS certificates on trusted LANs
- If your NAS has a valid certificate, set `VERIFY_SSL=true`
- Never disable certificate verification on untrusted networks

### HTTP exposure

- Prefer putting HTTP mode behind TLS termination or a reverse proxy
- Treat `HTTP_QUERY_TOKEN` as a lightweight shared secret, not a replacement for network-layer protection
- Do not expose the server directly to the public internet without additional access controls

## Architecture

```text
mcp-server-synology/
├── main.py
├── src/
│   ├── mcp_server.py
│   ├── auth/
│   ├── filestation/
│   ├── downloadstation/
│   ├── health/
│   ├── nfs/
│   └── usermanagement/
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```

### Transport selection

- `TRANSPORT=stdio` → local stdio MCP server
- `TRANSPORT=http` → streamable HTTP server at `HTTP_HOST:HTTP_PORT` + `HTTP_PATH`

## Testing

```bash
python -m pytest
```
