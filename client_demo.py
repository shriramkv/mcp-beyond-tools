"""
Demo client for DocVault.

Connects to the server over stdio and exercises all three primitives:
lists them, reads a resource, calls a tool, and fetches a prompt. Use this
to verify the server end-to-end without any AI host in the loop.

    python examples/client_demo.py
"""

import asyncio
import sys
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

REPO_ROOT = Path(__file__).resolve().parents[1]


async def main() -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "docvault.server"],
        cwd=str(REPO_ROOT),
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            print("=" * 60)
            print("1. THE THREE PRIMITIVES, AS THE HOST SEES THEM")
            print("=" * 60)

            tools = await session.list_tools()
            print(f"\nTools ({len(tools.tools)}):")
            for t in tools.tools:
                print(f"  - {t.name}")

            resources = await session.list_resources()
            print(f"\nResources ({len(resources.resources)}):")
            for r in resources.resources:
                print(f"  - {r.uri}")

            templates = await session.list_resource_templates()
            print(f"\nResource templates ({len(templates.resourceTemplates)}):")
            for rt in templates.resourceTemplates:
                print(f"  - {rt.uriTemplate}")

            prompts = await session.list_prompts()
            print(f"\nPrompts ({len(prompts.prompts)}):")
            for p in prompts.prompts:
                print(f"  - {p.name}")

            print()
            print("=" * 60)
            print("2. READ A RESOURCE (no tool call, no side effects)")
            print("=" * 60)
            content = await session.read_resource("docvault://docs/mcp-primitives")
            print(content.contents[0].text)

            print("=" * 60)
            print("3. CALL A TOOL (a genuine action: search)")
            print("=" * 60)
            result = await session.call_tool(
                "search_vault", {"query": "stateless", "max_results": 3}
            )
            print(result.content[0].text)

            print()
            print("=" * 60)
            print("4. FETCH A PROMPT (server-authored workflow)")
            print("=" * 60)
            prompt = await session.get_prompt(
                "summarise_document", {"name": "stateless-2026"}
            )
            print(prompt.messages[0].content.text)

            print()
            print("All three primitives exercised successfully.")


if __name__ == "__main__":
    asyncio.run(main())
