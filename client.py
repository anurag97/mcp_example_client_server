"""
HR Agent Client — Groq + LangGraph alternative to Claude Desktop

Usage:
    1. Start the MCP server:  uv run main.py
    2. In another terminal:   uv run client.py
"""

import asyncio
import os
import warnings
from typing import Any, Optional

import httpx
from dotenv import load_dotenv
from langchain_core.tools import StructuredTool
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from pydantic import create_model

# Suppress LangGraph v1 deprecation noise
warnings.filterwarnings("ignore", category=DeprecationWarning, module="langgraph")

load_dotenv()

MCP_SERVER_URL = "http://localhost:8000/mcp"

# -------------------------------------------------------------------
# Convert MCP tool definitions → LangChain StructuredTools
# -------------------------------------------------------------------

_JSON_TYPE_MAP = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
}


def _build_lc_tool(session: ClientSession, tool) -> StructuredTool:
    """Wrap a single MCP tool as a LangChain StructuredTool."""

    schema = tool.inputSchema or {}
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))

    fields: dict[str, Any] = {}
    for name, info in properties.items():
        py_type = _JSON_TYPE_MAP.get(info.get("type", "string"), str)
        if name in required:
            fields[name] = (py_type, ...)
        else:
            fields[name] = (Optional[py_type], None)

    ArgsModel = create_model(f"{tool.name}_args", **fields)

    async def _acall(**kwargs: Any) -> str:
        result = await session.call_tool(tool.name, arguments=kwargs)
        parts = []
        for content in result.content:
            if hasattr(content, "text"):
                parts.append(content.text)
        return "\n".join(parts) if parts else str(result.content)

    return StructuredTool(
        name=tool.name,
        description=tool.description or tool.name,
        args_schema=ArgsModel,
        coroutine=_acall,
        func=lambda **kw: asyncio.get_event_loop().run_until_complete(_acall(**kw)),
    )


# -------------------------------------------------------------------
# Main async loop
# -------------------------------------------------------------------

async def run_agent() -> None:
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise EnvironmentError(
            "GROQ_API_KEY not set. Add it to a .env file or export it."
        )

    # verify=False works around corporate SSL-inspection proxies that inject
    # self-signed certificates into the chain.
    llm = ChatGroq(
       model="openai/gpt-oss-120b",
        temperature=0,
        http_async_client=httpx.AsyncClient(verify=False),
    )

    print(f"Connecting to MCP server at {MCP_SERVER_URL} …")

    async with streamablehttp_client(MCP_SERVER_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_resp = await session.list_tools()
            lc_tools = [_build_lc_tool(session, t) for t in tools_resp.tools]

            print(f"Loaded {len(lc_tools)} tool(s): {[t.name for t in lc_tools]}")
            print("\nHR Leave Management Agent  |  type 'quit' to exit")
            print("=" * 55)

            agent = create_react_agent(llm, lc_tools)

            while True:
                try:
                    user_input = input("\nYou: ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nGoodbye!")
                    break

                if not user_input:
                    continue
                if user_input.lower() in ("quit", "exit", "q"):
                    print("Goodbye!")
                    break

                result = await agent.ainvoke(
                    {"messages": [("human", user_input)]}
                )
                print(f"\nAgent: {result['messages'][-1].content}")


if __name__ == "__main__":
    asyncio.run(run_agent())