# Changelog

## Unreleased

- Replaced the Xiaozhi/WebSocket bridge with first-class stdio and streamable HTTP transport selection.
- Added `TRANSPORT`, `HTTP_HOST`, `HTTP_PORT`, `HTTP_PATH`, and `HTTP_QUERY_TOKEN`.
- Bumped the minimum supported `mcp` SDK version to `1.27.0` to guarantee streamable HTTP support.
