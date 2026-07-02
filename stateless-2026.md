# The Stateless Shift

The 2026-07-28 specification removes protocol-level sessions from the
Streamable HTTP transport. Servers that assume a long-lived session or route
on the Mcp-Session-Id header must migrate before adopting the new revision.
