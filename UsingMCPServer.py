import os
import sys
import json
import asyncio
import traceback
import subprocess
from contextlib import suppress

# ==== TOGGLES ================================================================
RUN_WEBSOCKET_HANDSHAKE_DEMO = True   # Keep your previous handshake demo
RUN_SMOLAGENTS_STDIO_AGENT   = True   # Run your original smolagents + Stdio MCP flow
# ============================================================================

# --- Optional: smolagents + stdio MCP imports (guarded) ---------------------
try:
    from smolagents import ToolCollection, CodeAgent, InferenceClientModel
    from mcp import StdioServerParameters
    SMOLAGENTS_AVAILABLE = True
except Exception:
    SMOLAGENTS_AVAILABLE = False

# --- WebSocket MCP client imports (for demo) --------------------------------
try:
    from mcp.client.websocket import websocket_client
    from mcp.shared.message import SessionMessage
    from mcp.types import (
        JSONRPCRequest,
        InitializeRequest,
        InitializeRequestParams,
        Implementation,
        ClientCapabilities,
    )
    WEBSOCKET_MCP_AVAILABLE = True
except Exception:
    WEBSOCKET_MCP_AVAILABLE = False

# ======================= Embedded WebSocket MCP server =======================
WEBSOCKET_SERVER_SCRIPT = r"""
import asyncio
import json
import contextlib
import websockets

# Compatible handler signature across websockets versions
async def mcp_server(websocket, *_) -> None:
    try:
        # Wait for the client's initialize request (with timeout)
        raw = await asyncio.wait_for(websocket.recv(), timeout=15)
        req = json.loads(raw)

        if req.get("method") != "initialize":
            await websocket.close(code=1002, reason="Expected 'initialize'")
            return

        # Minimal MCP initialize response
        init_resp = {
            "jsonrpc": "2.0",
            "id": req.get("id"),
            "result": {
                "protocolVersion": "2025-06-18",
                "serverInfo": {"name": "Test WebSocket Server", "version": "1.0"},
                "capabilities": {"tools": {"listChanged": False}},
            },
        }
        await websocket.send(json.dumps(init_resp))

        # Optionally accept a follow-up notification (e.g., 'initialized')
        with contextlib.suppress(asyncio.TimeoutError):
            _ = await asyncio.wait_for(websocket.recv(), timeout=2)

        # Keep the connection alive until client closes
        await websocket.wait_closed()

    except Exception:
        with contextlib.suppress(Exception):
            await websocket.close()

async def main():
    # Enforce MCP subprotocol (comment out subprotocols to relax during testing)
    async with websockets.serve(mcp_server, "localhost", 8765, subprotocols=["mcp"]):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())
"""

async def start_ws_server() -> subprocess.Popen:
    with open("websocket_server.py", "w", encoding="utf-8") as f:
        f.write(WEBSOCKET_SERVER_SCRIPT)
    return subprocess.Popen([sys.executable, "-u", "websocket_server.py"])

async def run_ws_client_demo():
    if not WEBSOCKET_MCP_AVAILABLE:
        print("WebSocket MCP client packages not available; skipping the handshake demo.")
        return

    print("Connecting to WebSocket server…")
    async with websocket_client("ws://localhost:8765") as (read_stream, write_stream):
        print("Connected. Sending MCP initialize…")

        init_request = InitializeRequest(
            params=InitializeRequestParams(
                protocolVersion="2025-06-18",
                clientInfo=Implementation(name="TestClient", version="1.0"),
                capabilities=ClientCapabilities(),
            )
        )

        msg = SessionMessage(
            message=JSONRPCRequest(
                jsonrpc="2.0",
                id=1,
                **init_request.model_dump(),  # includes method="initialize", params={...}
            )
        )
        await write_stream.send(msg)

        init_response = await asyncio.wait_for(read_stream.receive(), timeout=15)
        print("Received initialize response:")
        try:
            payload = getattr(init_response, "message", init_response)
            as_dict = (
                payload.dict()
                if hasattr(payload, "dict")
                else (payload.model_dump() if hasattr(payload, "model_dump") else payload)
            )
            print(json.dumps(as_dict, indent=2, default=str))
        except Exception:
            print(init_response)

        print("\nMCP WebSocket connection established ✅")
        await asyncio.sleep(1)

# ===================== smolagents + stdio MCP integration ====================

async def run_smolagents_stdio_agent():
    """
    This is your original code path, integrated as-is.
    It launches a real MCP server (pubmedmcp) over stdio via `uvx`,
    then builds a ToolCollection, creates a CodeAgent, and runs the prompt.
    """
    if not SMOLAGENTS_AVAILABLE:
        print(
            "\n[smolagents] not available. Please install dependencies, e.g.:\n"
            "  pip install smolagents mcp\n"
            "and ensure `uvx` is available (pipx install uv, or install uvx via uv)."
        )
        return

    # Model can be changed if desired
    model = InferenceClientModel("Qwen/Qwen2.5-Coder-32B-Instruct")

    # Your original stdio MCP server parameters (unchanged)
    server_parameters = StdioServerParameters(
        command="uvx",
        args=["--quiet", "pubmedmcp@0.1.3"],
        env={"UV_PYTHON": "3.12", **os.environ},
    )

    print("\nStarting smolagents + stdio MCP server (pubmedmcp)…")
    # ToolCollection.from_mcp will spawn the stdio MCP server and manage its lifecycle.
    try:
        with ToolCollection.from_mcp(server_parameters, trust_remote_code=True) as tool_collection:
            print(f"Loaded {len(tool_collection.tools)} MCP tool(s) from pubmedmcp.")
            agent = CodeAgent(tools=[*tool_collection.tools], model=model, add_base_tools=True)

            # Your original test prompt
            prompt = "Please find a remedy for hangover."
            print(f"\nRunning agent with prompt: {prompt!r}\n")
            result = agent.run(prompt)  # Typically returns the final text
            if result is not None:
                print("\n=== Agent Result ===\n")
                print(result)
            else:
                print("\nAgent finished without a return payload.")
    except FileNotFoundError as e:
        print(
            "\nFailed to start MCP server via `uvx`. Make sure `uvx` is installed and on PATH.\n"
            " - Install uvx: https://docs.astral.sh/uv/guides/tools/\n"
            " - Or try: pipx install uv\n"
            f"Details: {e}"
        )
    except Exception as e:
        print(f"\nError running smolagents agent: {type(e).__name__}: {e}")
        traceback.print_exc()

# ================================ main() =====================================

async def main():
    server = None
    try:
        if RUN_WEBSOCKET_HANDSHAKE_DEMO and WEBSOCKET_MCP_AVAILABLE:
            print("Starting WebSocket MCP server…")
            server = await start_ws_server()
            await asyncio.sleep(0.8)  # brief boot wait
            await run_ws_client_demo()
        elif RUN_WEBSOCKET_HANDSHAKE_DEMO:
            print("WebSocket MCP client libraries missing; skipping handshake demo.")

        if RUN_SMOLAGENTS_STDIO_AGENT:
            await run_smolagents_stdio_agent()

    except Exception as e:
        print(f"\nAn error occurred: {type(e).__name__}: {e}")
        traceback.print_exc()
    finally:
        if server:
            print("\nTerminating WebSocket MCP server process…")
            with suppress(Exception):
                server.terminate()
            with suppress(Exception):
                server.wait(timeout=5)
        with suppress(FileNotFoundError):
            os.remove("websocket_server.py")

if __name__ == "__main__":
    asyncio.run(main())
