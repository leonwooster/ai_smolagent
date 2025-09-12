# UsingMCPServer.py - Prerequisites and Setup Guide

This document outlines the prerequisites and setup steps required to run `UsingMCPServer.py`, which demonstrates MCP (Model Context Protocol) server integration with smolagents.

## Prerequisites

### 1. Python Environment
- **Python 3.8+** (recommended: Python 3.11 or 3.12)
- Virtual environment recommended

### 2. Required Python Packages

Install the following packages in your Python environment:

```bash
pip install smolagents mcp websockets anyio pydantic
```

Or if you have a `requirements.txt`:
```bash
pip install -r requirements.txt
```

### 3. UV/UVX Installation (Critical for MCP Server)

The script uses `uvx` to run MCP servers. You must install UV/UVX:

#### Option 1: Install via pipx (Recommended)
```bash
# Install pipx if not already installed
python -m pip install -U pipx

# Restart your shell, then install uv
pipx install uv

# Ensure paths are properly set
pipx ensurepath
```

#### Option 2: Direct UV installation
Follow the official UV installation guide: https://docs.astral.sh/uv/getting-started/installation/

### 4. Verify UVX Installation

After installation, verify `uvx` is available:
```bash
uvx --version
```

If the command is not found, ensure `%USERPROFILE%\.local\bin` (Windows) or `~/.local/bin` (Linux/Mac) is in your PATH.

### 5. Network Requirements

- Port 8765 must be available for the WebSocket server demo
- Internet connection required to download MCP servers via `uvx`

## Configuration Options

The script has two main toggle options at the top:

```python
RUN_WEBSOCKET_HANDSHAKE_DEMO = True   # WebSocket MCP handshake demo
RUN_SMOLAGENTS_STDIO_AGENT   = True   # smolagents + stdio MCP integration
```

Set these to `True`/`False` based on what you want to test.

## Running the Script

Once prerequisites are met:

```bash
python UsingMCPServer.py
```

## Expected Behavior

### WebSocket Demo (if enabled)
1. Starts a local WebSocket MCP server on port 8765
2. Connects to it and performs MCP initialization handshake
3. Displays the connection success message

### smolagents Integration (if enabled)
1. Launches `pubmedmcp@0.1.3` server via `uvx`
2. Creates a ToolCollection from the MCP server
3. Initializes a CodeAgent with the MCP tools
4. Runs a test prompt: "Please find a remedy for hangover."

## Troubleshooting

### "uvx command not found"
- Ensure UV is properly installed and in PATH
- Try restarting your terminal/shell
- Run `pipx ensurepath` to update PATH variables

### "Failed to start MCP server"
- Verify internet connection (needed to download MCP servers)
- Check that `uvx` can run: `uvx --help`
- Ensure Python 3.12 is available (specified in UV_PYTHON environment variable)

### WebSocket connection errors
- Ensure port 8765 is not in use by other applications
- Check firewall settings if running on a restricted network

### Import errors
- Verify all required packages are installed in the correct Python environment
- Check that you're using the right virtual environment

## Model Configuration

The script uses `Qwen/Qwen2.5-Coder-32B-Instruct` by default. You can modify this in the code:

```python
model = InferenceClientModel("your-preferred-model")
```

## File Structure

After running, the script may create temporary files:
- `websocket_server.py` (automatically cleaned up)

These are automatically removed when the script exits.
