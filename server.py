"""
DocVault: a reference MCP server that uses ALL THREE primitives correctly.

The point of this server is pedagogical. Most MCP servers in the wild expose
everything as a tool, even plain data reads. That forces the host through a
code-execution consent flow for what should have been a simple read, bloats
the model's context with tool schemas, and makes auditing harder.

The rule of thumb demonstrated here:

    RESOURCES  -> read-only context (documents, listings). No side effects.
    TOOLS      -> actions with side effects or real computation (search, write).
    PROMPTS    -> reusable, parameterised interaction templates.

Companion blog: "The Unknowns of MCP: What Most Developers Still Haven't
Noticed" (AAIF Ambassador series).

Run over stdio (default):

    python -m docvault.server

Author: Shriram K Vasudevan (@shriramkv)
Licence: MIT
"""

from __future__ import annotations

import datetime
import re
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

VAULT_DIR = Path(__file__).parent / "sample_docs"
VAULT_DIR.mkdir(exist_ok=True)

mcp = FastMCP(
    "docvault",
    instructions=(
        "DocVault is a local document vault. Read documents through the "
        "docvault:// resources, act on the vault through the tools, and use "
        "the prompts for common document workflows."
    ),
)


def _safe_doc_path(name: str) -> Path:
    """Resolve a document name inside the vault, refusing path traversal."""
    if not re.fullmatch(r"[A-Za-z0-9_\-]+", name):
        raise ValueError(
            "Document names may only contain letters, digits, hyphens and "
            "underscores."
        )
    return VAULT_DIR / f"{name}.md"


# ---------------------------------------------------------------------------
# RESOURCES: read-only context. No side effects, no consent ceremony needed.
#
# A common anti-pattern is a `read_document(name)` TOOL. A read has no side
# effects, so it belongs here. The host can fetch, cache, and attach these
# without treating them as code execution.
# ---------------------------------------------------------------------------


@mcp.resource("docvault://docs")
def list_documents() -> str:
    """Catalogue of every document currently in the vault."""
    docs = sorted(VAULT_DIR.glob("*.md"))
    if not docs:
        return "The vault is empty."
    lines = ["# DocVault catalogue", ""]
    for doc in docs:
        stat = doc.stat()
        modified = datetime.datetime.fromtimestamp(stat.st_mtime).strftime(
            "%Y-%m-%d %H:%M"
        )
        lines.append(f"- **{doc.stem}** ({stat.st_size} bytes, modified {modified})")
    return "\n".join(lines)


@mcp.resource("docvault://docs/{name}")
def read_document(name: str) -> str:
    """Full content of a single document in the vault."""
    path = _safe_doc_path(name)
    if not path.exists():
        raise FileNotFoundError(
            f"No document named '{name}'. Read docvault://docs for the catalogue."
        )
    return path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# TOOLS: actions. Side effects (writing) or real computation (searching).
#
# Note what is NOT here: no read_document tool, no list_documents tool.
# Reads are resources. Keeping tools to genuine actions keeps the tool list
# short, which is exactly the "context economics" problem the companion blog
# describes.
# ---------------------------------------------------------------------------


@mcp.tool()
def search_vault(query: str, max_results: int = 5) -> str:
    """Search every document in the vault for a query string.

    Returns matching lines with their document name and line number, so the
    model can follow up by reading the right docvault://docs/{name} resource.
    """
    query_lower = query.lower()
    hits: list[str] = []
    for doc in sorted(VAULT_DIR.glob("*.md")):
        for line_no, line in enumerate(
            doc.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if query_lower in line.lower():
                hits.append(f"{doc.stem}:{line_no}: {line.strip()}")
                if len(hits) >= max_results:
                    break
        if len(hits) >= max_results:
            break
    if not hits:
        return f"No matches for '{query}'."
    return "\n".join(hits)


@mcp.tool()
def add_note(name: str, content: str) -> str:
    """Create a new note in the vault, or append to an existing one.

    This is a genuine side effect, which is exactly why it is a tool and not
    a resource: the host should put a consent flow in front of it.
    """
    path = _safe_doc_path(name)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    if path.exists():
        with path.open("a", encoding="utf-8") as fh:
            fh.write(f"\n\n---\n*Appended {stamp}*\n\n{content}\n")
        return f"Appended to existing note '{name}'."
    path.write_text(f"# {name}\n\n*Created {stamp}*\n\n{content}\n", encoding="utf-8")
    return f"Created new note '{name}'."


# ---------------------------------------------------------------------------
# PROMPTS: reusable, parameterised interaction templates.
#
# Prompts let the SERVER encode its own best-practice workflows, so every
# host gets them for free instead of every user reinventing them.
# ---------------------------------------------------------------------------


@mcp.prompt()
def summarise_document(name: str) -> str:
    """A structured summarisation workflow for one vault document."""
    return (
        f"Read the resource docvault://docs/{name} and produce a summary with "
        "three sections: (1) one-paragraph overview, (2) the three most "
        "important points as short sentences, (3) any open questions or "
        "action items the document implies. Use British spelling."
    )


@mcp.prompt()
def compare_documents(first: str, second: str) -> str:
    """A structured comparison workflow across two vault documents."""
    return (
        f"Read the resources docvault://docs/{first} and "
        f"docvault://docs/{second}. Compare them under three headings: "
        "shared ground, genuine disagreements, and gaps (things one covers "
        "that the other ignores). Close with a recommendation on which "
        "document needs updating."
    )


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
