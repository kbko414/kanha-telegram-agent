import json
import aiohttp
from config import API_BASE, API_KEY, MODEL, MAX_TOOL_ROUNDS
from tools import TOOL_SCHEMAS, execute_tool

async def chat_completion(messages, temperature=0.8, tools=True):
    url = f"{API_BASE.rstrip('/')}/chat/completions"
    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
        # Small context keeps KV-cache RAM low on small VPS boxes.
        "options": {"num_ctx": 4096},
    }
    if tools:
        payload["tools"] = TOOL_SCHEMAS
        payload["tool_choice"] = "auto"
    headers = {"Content-Type": "application/json"}
    if API_KEY and API_KEY not in ("sk-no-key", ""):
        headers["Authorization"] = f"Bearer {API_KEY}"
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=180)) as s:
        async with s.post(url, json=payload, headers=headers) as r:
            if r.status != 200:
                return {"error": f"[{r.status}] {(await r.text())[:500]}"}
            return await r.json()

async def run_agent(history, temperature=0.8):
    msgs = list(history)
    for _ in range(MAX_TOOL_ROUNDS):
        resp = await chat_completion(msgs, temperature, tools=True)
        if "error" in resp: return resp["error"], msgs
        choice = resp["choices"][0]["message"]
        msgs.append(choice)
        tool_calls = choice.get("tool_calls") or []
        if not tool_calls:
            return choice.get("content", "") or "(empty)", msgs
        for tc in tool_calls:
            try: args = json.loads(tc["function"]["arguments"] or "{}")
            except json.JSONDecodeError: args = {}
            result = await execute_tool(tc["function"]["name"], args)
            msgs.append({"role": "tool", "tool_call_id": tc["id"], "content": result})
    resp = await chat_completion(msgs, temperature, tools=False)
    if "error" in resp: return resp["error"], msgs
    final = resp["choices"][0]["message"]
    msgs.append(final)
    return final.get("content", "") or "(empty)", msgs
