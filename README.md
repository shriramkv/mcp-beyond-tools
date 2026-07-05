# mcp-beyond-tools

**A reference MCP server that uses all three primitives correctly: tools, resources, and prompts.**

Most MCP servers in the wild expose everything as a tool, even plain data reads. That forces the host through a code-execution consent flow for what should have been a simple read, bloats the model's context window with tool schemas, and makes auditing harder. This repository is a small, complete, tested server (**DocVault**, a local document vault) built to demonstrate the correct split.

This is the code companion to the AAIF Ambassador blog post *"The Unknowns of MCP: What Most Developers Still Haven't Noticed"*, specifically Unknown 1 (tools are only one of the primitives) and Unknown 6 (context economics).

## The rule of thumb this repo demonstrates

| Primitive | Use it for | DocVault examples |
|---|---|---|
| **Resource** | Read-only context, no side effects | `docvault://docs` (catalogue), `docvault://docs/{name}` (document content) |
| **Tool** | Actions: side effects or real computation | `search_vault`, `add_note` |
| **Prompt** | Reusable, parameterised workflows the server authors | `summarise_document`, `compare_documents` |

Note what is deliberately absent: there is no `read_document` tool and no `list_documents` tool. Reads are resources. Keeping the tool list down to genuine actions is what keeps your context window lean when a host connects many servers at once.

## Quickstart

Requires Python 3.10+.

```bash
git clone https://github.com/shriramkv/mcp-beyond-tools.git
cd mcp-beyond-tools
pip install -r requirements.txt

# Run the end-to-end demo client (no AI host needed)
python examples/client_demo.py
```

The demo client connects over stdio, lists all three primitives, reads a resource, calls a tool, and fetches a prompt. Expected final line:

```
All three primitives exercised successfully.
```

## Using it from Claude Desktop

Add this to your `claude_desktop_config.json` (adjust the path):

```json
{
  "mcpServers": {
    "docvault": {
      "command": "python",
      "args": ["-m", "docvault.server"],
      "cwd": "/absolute/path/to/mcp-beyond-tools"
    }
  }
}
```

Restart Claude Desktop. You will see two tools, the document resources, and two prompts. Try: *"Search the vault for 'stateless' and then read the matching document."* Watch how the search goes through a tool call while the read arrives as a resource.

## Repository structure

```
mcp-beyond-tools/
├── docvault/
│   ├── server.py          # the server: 2 resources, 2 tools, 2 prompts
│   └── sample_docs/       # seed documents served as resources
├── examples/
│   └── client_demo.py     # stdio client exercising every primitive
├── requirements.txt
└── LICENSE                # MIT
```

## Why this matters (the short version)

1. **Security and consent.** Tools represent code execution and deserve a consent flow. Reads do not. Modelling reads as resources means the consent ceremony is reserved for things that can actually change state.
2. **Context economics.** Every tool schema you expose is context the model pays for on every turn. Two tools instead of five is a real saving once a host connects twenty servers.
3. **Auditability.** When the tool list contains only actions, the audit log of tool calls becomes a log of things that happened, not a log of things that were merely looked at.

## Author

Shriram K Vasudevan ([@shriramkv](https://github.com/shriramkv))
YouTube: https://www.youtube.com/shriramvasudevan

Licensed under MIT.
