"""CLI entrypoint placeholder."""

from __future__ import annotations

import os
import sys
from pathlib import Path
import json
import re

from .skill_loader import SkillLoader
from .tools import apply_edit, eval_math_expr, execute_tool, preview_edit, tool_specs

from .openrouter_client import call_model


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip("\"'")  # allow simple quoted values
        if key and key not in os.environ:
            os.environ[key] = value


def load_config() -> dict[str, str]:
    load_dotenv(Path(".env"))
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1").strip()
    model = os.getenv("OPENROUTER_MODEL", "openrouter/auto").strip()

    if not api_key:
        print("Error: OPENROUTER_API_KEY is required.", file=sys.stderr)
        print("Tip: set it in your shell or create a local .env and load it.", file=sys.stderr)
        raise SystemExit(1)

    if not model:
        print("Error: OPENROUTER_MODEL is required.", file=sys.stderr)
        raise SystemExit(1)

    return {"api_key": api_key, "base_url": base_url, "model": model}


def _parse_json_tool_call(text: str) -> tuple[str, dict] | None:
    match = re.search(r"```json\\s*(\\{.*?\\})\\s*```", text, flags=re.S)
    if not match:
        return None
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    if payload.get("method") != "calculator":
        return None
    params = payload.get("params", {})
    return "calculator", params


def _parse_inline_tool_call(content: object) -> tuple[str, dict] | None:
    if isinstance(content, list) and content:
        first = content[0]
        if isinstance(first, dict) and "name" in first and "arguments" in first:
            return first["name"], first["arguments"]
    if isinstance(content, str) and content.strip().startswith(("{", "[")):
        try:
            payload = json.loads(content)
        except json.JSONDecodeError:
            return None
        if isinstance(payload, list) and payload and "name" in payload[0]:
            return payload[0]["name"], payload[0].get("arguments", {})
        if isinstance(payload, dict) and "name" in payload:
            return payload["name"], payload.get("arguments", {})
    return None


def main() -> None:
    config = load_config()
    skill_loader = SkillLoader("skills")
    loaded_skills = skill_loader.discover_skills()
    system_message = {
        "role": "system",
        "content": (
            "You are a helpful assistant. "
            "When using tools, do not precompute or transform math expressions into numbers. "
            "Only call tools with the original expression. "
            "When a tool is needed, you must use tool_calls and never output JSON in plain text. "
            "Before editing a file, you must read it. After editing, read it again to verify changes."
        ),
    }
    metadata_prompt = skill_loader.get_skills_metadata_prompt()
    if metadata_prompt:
        system_message["content"] = f"{system_message['content']}\n\n{metadata_prompt}"
    history: list[dict[str, str]] = []
    get_skill_tool = {
        "type": "function",
        "function": {
            "name": "get_skill",
            "description": "Load full content for a specific skill by skill name.",
            "parameters": {
                "type": "object",
                "properties": {"skill_name": {"type": "string"}},
                "required": ["skill_name"],
            },
        },
    }

    def active_tool_specs() -> list[dict]:
        return [*tool_specs(), get_skill_tool]

    initial_prompt = "Say '你好' and nothing else."
    if len(sys.argv) > 1:
        initial_prompt = " ".join(sys.argv[1:]).strip()

    def run_turn(user_text: str) -> None:
        history.append({"role": "user", "content": user_text})
        if os.getenv("DEBUG", "").lower() in {"1", "true", "yes"}:
            print("DEBUG loaded_skills:", [s.name for s in loaded_skills])
            if metadata_prompt:
                print("DEBUG skills_metadata_prompt:", metadata_prompt)
            print(
                "DEBUG new_messages:",
                [system_message, {"role": "user", "content": user_text}],
            )
            print("DEBUG tools:", active_tool_specs())

        max_tool_rounds = 15
        rounds = 0
        while True:
            response_json = call_model(
                api_key=config["api_key"],
                base_url=config["base_url"],
                model=config["model"],
                messages=[system_message, *history],
                tools=active_tool_specs(),
            )
            choice = response_json["choices"][0]["message"]
            tool_calls = choice.get("tool_calls") or []

            if tool_calls:
                history.append({"role": "assistant", "content": choice.get("content", ""), "tool_calls": tool_calls})
                current_tool_results: list[dict[str, str]] = []
                for call in tool_calls:
                    name = call["function"]["name"]
                    args = json.loads(call["function"]["arguments"] or "{}")
                    if name == "get_skill":
                        skill_name = str(args.get("skill_name", "")).strip()
                        skill = skill_loader.get_skill(skill_name)
                        if not skill:
                            result = f"error: skill not found: {skill_name}"
                        else:
                            result = skill.full_prompt()
                    elif name == "edit_file":
                        path = str(args.get("path", ""))
                        target = str(args.get("target", ""))
                        replacement = str(args.get("replacement", ""))
                        preview = preview_edit(path, target, replacement)
                        if not preview:
                            result = "error: edit preview failed"
                        else:
                            diff, updated = preview
                            print("EDIT PREVIEW:\n" + diff)
                            confirm = input("Apply this change? (yes/no) ").strip().lower()
                            if confirm in {"y", "yes"}:
                                result = apply_edit(path, updated)
                            else:
                                result = "canceled"
                    else:
                        result = execute_tool(name, args)
                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "content": result,
                    }
                    history.append(tool_msg)
                    current_tool_results.append(tool_msg)
                if os.getenv("DEBUG", "").lower() in {"1", "true", "yes"}:
                    print("DEBUG tool_calls:", tool_calls)
                    print("DEBUG tool_results:", current_tool_results)
                    print(
                        "DEBUG new_messages:",
                        [
                            {"role": "assistant", "content": choice.get("content", ""), "tool_calls": tool_calls},
                            *current_tool_results,
                        ],
                    )
                rounds += 1
                if rounds >= max_tool_rounds:
                    print("error: too many tool calls")
                    return
                continue

            response_content = choice.get("content", "")
            if isinstance(response_content, str):
                response_text = response_content.strip()
            else:
                response_text = ""
            tool_call = None
            if isinstance(response_content, str) and response_text.startswith("```") and "calculator" in response_text:
                tool_call = _parse_json_tool_call(response_text)
            if not tool_call:
                tool_call = _parse_inline_tool_call(response_content)
            if tool_call:
                name, args = tool_call
                if name == "get_skill":
                    skill_name = str(args.get("skill_name", "")).strip()
                    skill = skill_loader.get_skill(skill_name)
                    if not skill:
                        result = f"error: skill not found: {skill_name}"
                    else:
                        result = skill.full_prompt()
                else:
                    result = execute_tool(name, args)
                print(result)
                history.append({"role": "assistant", "content": response_content})
                history.append({"role": "tool", "content": result})
                return
            response = response_text
            print(response)
            history.append({"role": "assistant", "content": response})
            return

    run_turn(initial_prompt)

    while True:
        try:
            user_text = input("> ").strip()
        except EOFError:
            print()
            break
        if not user_text:
            continue
        if user_text.lower() in {"exit", "quit"}:
            break
        run_turn(user_text)


if __name__ == "__main__":
    main()
