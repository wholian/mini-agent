"""Minimal OpenRouter client using requests."""

from __future__ import annotations

import json
import os
from typing import Any

import requests


def call_model(
    *,
    api_key: str,
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
    }
    if tools:
        payload["tools"] = tools
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        # Optional but recommended by OpenRouter
        "HTTP-Referer": "http://localhost",
        "X-Title": "mini-agent",
    }

    resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
    resp.raise_for_status()
    parsed = resp.json()
    if os.getenv("DEBUG", "").lower() in {"1", "true", "yes"}:
        message = parsed["choices"][0]["message"]
        content = message.get("content", "")
        print("DEBUG response_message:", content)
        if message.get("tool_calls"):
            print("DEBUG response_tool_calls:", message["tool_calls"])
    return parsed
