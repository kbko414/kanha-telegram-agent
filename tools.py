import asyncio
import subprocess
from pathlib import Path
import aiohttp
from config import WORK_DIR, SHELL_TIMEOUT

TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "shell",
        "description": "Run a shell command on the host. Returns stdout+stderr.",
        "parameters": {"type": "object",
            "properties": {"command": {"type": "string"}},
            "required": ["command"]}}},
    {"type": "function", "function": {
        "name": "read_file",
        "description": "Read a file. Relative paths resolve under work/.",
        "parameters": {"type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"]}}},
    {"type": "function", "function": {
        "name": "write_file",
        "description": "Write content to a file. Relative paths resolve under work/.",
        "parameters": {"type": "object",
            "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
            "required": ["path", "content"]}}},
    {"type": "function", "function": {
        "name": "list_dir",
        "description": "List a directory. Default: work/.",
        "parameters": {"type": "object", "properties": {"path": {"type": "string"}}}}},
    {"type": "function", "function": {
        "name": "web_fetch",
        "description": "Fetch a URL, return text (truncated to 8KB).",
        "parameters": {"type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"]}}},
]

def _resolve(p: str) -> Path:
    path = Path(p)
    return path if path.is_absolute() else WORK_DIR / path

async def tool_shell(command: str) -> str:
    try:
        proc = await asyncio.create_subprocess_shell(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            cwd=str(WORK_DIR))
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=SHELL_TIMEOUT)
        text = out.decode("utf-8", "replace")
        return text[-8000:] if len(text) > 8000 else text
    except asyncio.TimeoutError:
        return f"[timeout after {SHELL_TIMEOUT}s]"
    except Exception as e:
        return f"[shell error] {e}"

async def tool_read_file(path: str) -> str:
    try:
        return _resolve(path).read_bytes()[:16000].decode("utf-8", "replace")
    except Exception as e:
        return f"[read error] {e}"

async def tool_write_file(path: str, content: str) -> str:
    try:
        p = _resolve(path); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"wrote {len(content)} bytes to {p}"
    except Exception as e:
        return f"[write error] {e}"

async def tool_list_dir(path: str = "") -> str:
    try:
        p = _resolve(path or ".")
        return "\n".join(f"{'d' if c.is_dir() else 'f'} {c.name}" for c in sorted(p.iterdir())) or "(empty)"
    except Exception as e:
        return f"[list error] {e}"

async def tool_web_fetch(url: str) -> str:
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as s:
            async with s.get(url, headers={"User-Agent": "Mozilla/5.0"}) as r:
                return (await r.text())[:8000]
    except Exception as e:
        return f"[fetch error] {e}"

TOOL_DISPATCH = {
    "shell":      lambda a: tool_shell(a.get("command", "")),
    "read_file":  lambda a: tool_read_file(a.get("path", "")),
    "write_file": lambda a: tool_write_file(a.get("path", ""), a.get("content", "")),
    "list_dir":   lambda a: tool_list_dir(a.get("path", "")),
    "web_fetch":  lambda a: tool_web_fetch(a.get("url", "")),
}

async def execute_tool(name: str, args: dict) -> str:
    fn = TOOL_DISPATCH.get(name)
    return await fn(args) if fn else f"[unknown tool: {name}]"
