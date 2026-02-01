"""Tool definitions and registry."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import difflib
import subprocess
import ast
import operator


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    parameters: dict


_OPS: dict[type[ast.AST], object] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}


def eval_math_expr(expr: str) -> float:
    node = ast.parse(expr, mode="eval")

    def _eval(n: ast.AST) -> float:
        if isinstance(n, ast.Expression):
            return _eval(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return float(n.value)
        if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
            val = _eval(n.operand)
            return val if isinstance(n.op, ast.UAdd) else -val
        if isinstance(n, ast.BinOp) and type(n.op) in _OPS:
            left = _eval(n.left)
            right = _eval(n.right)
            return _OPS[type(n.op)](left, right)  # type: ignore[operator]
        raise ValueError("Unsupported expression")

    return _eval(node)


CALCULATOR = ToolSpec(
    name="calculator",
    description="Evaluate a basic math expression (numbers and + - * / % ** with parentheses).",
    parameters={
        "type": "object",
        "properties": {"expression": {"type": "string"}},
        "required": ["expression"],
    },
)

READ_FILE = ToolSpec(
    name="read_file",
    description="Read a text file from the project workspace by relative path.",
    parameters={
        "type": "object",
        "properties": {"path": {"type": "string"}},
        "required": ["path"],
    },
)

WRITE_FILE = ToolSpec(
    name="write_file",
    description="Write text content to a file in the project workspace by relative path.",
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"},
        },
        "required": ["path", "content"],
    },
)

EDIT_FILE = ToolSpec(
    name="edit_file",
    description=(
        "Edit a file by replacing the first occurrence of a target string with a replacement string. "
        "This tool will show a diff and requires user confirmation."
    ),
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "target": {"type": "string"},
            "replacement": {"type": "string"},
        },
        "required": ["path", "target", "replacement"],
    },
)

RUN_SHELL = ToolSpec(
    name="run_shell",
    description="Run a shell command in the project root and return stdout/stderr.",
    parameters={
        "type": "object",
        "properties": {
            "command": {"type": "string"},
        },
        "required": ["command"],
    },
)


TOOLS: dict[str, ToolSpec] = {
    CALCULATOR.name: CALCULATOR,
    READ_FILE.name: READ_FILE,
    WRITE_FILE.name: WRITE_FILE,
    EDIT_FILE.name: EDIT_FILE,
    RUN_SHELL.name: RUN_SHELL,
}


def tool_specs() -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters,
            },
        }
        for tool in TOOLS.values()
    ]


def execute_tool(name: str, arguments: dict) -> str:
    base_dir = Path.cwd().resolve()

    def _resolve_path(path_str: str) -> Path | None:
        if not path_str:
            return None
        path = Path(path_str)
        full = (base_dir / path).resolve() if not path.is_absolute() else path.resolve()
        if base_dir not in full.parents and full != base_dir:
            return None
        return full

    if name == "calculator":
        expr = str(arguments.get("expression", ""))
        try:
            result = eval_math_expr(expr)
            return str(result)
        except Exception:
            return "error: unsupported expression"
    if name == "read_file":
        path = _resolve_path(str(arguments.get("path", "")))
        if not path or not path.exists() or not path.is_file():
            return "error: file not found or invalid path"
        return path.read_text(encoding="utf-8")
    if name == "write_file":
        path = _resolve_path(str(arguments.get("path", "")))
        content = str(arguments.get("content", ""))
        if not path:
            return "error: invalid path"
        if not path.parent.exists():
            return "error: parent directory does not exist"
        path.write_text(content, encoding="utf-8")
        return "ok"
    if name == "edit_file":
        target = str(arguments.get("target", ""))
        replacement = str(arguments.get("replacement", ""))
        preview = preview_edit(str(arguments.get("path", "")), target, replacement)
        if not preview:
            return "error: edit preview failed"
        diff, _updated = preview
        return f"preview:\n{diff}"
    if name == "run_shell":
        command = str(arguments.get("command", "")).strip()
        if not command:
            return "error: command must be non-empty"
        proc = subprocess.run(
            command,
            shell=True,
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return f"exit_code: {proc.returncode}\nstdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
    return "error: unknown tool"


def resolve_path(path_str: str) -> Path | None:
    base_dir = Path.cwd().resolve()
    if not path_str:
        return None
    path = Path(path_str)
    full = (base_dir / path).resolve() if not path.is_absolute() else path.resolve()
    if base_dir not in full.parents and full != base_dir:
        return None
    return full


def preview_edit(path_str: str, target: str, replacement: str) -> tuple[str, str] | None:
    path = resolve_path(path_str)
    if not path or not path.exists() or not path.is_file():
        return None
    if target == "":
        return None
    text = path.read_text(encoding="utf-8")
    if target not in text:
        return None
    updated = text.replace(target, replacement, 1)
    diff = "\n".join(
        difflib.unified_diff(
            text.splitlines(),
            updated.splitlines(),
            fromfile=str(path_str),
            tofile=str(path_str),
            lineterm="",
        )
    )
    return diff, updated


def apply_edit(path_str: str, updated: str) -> str:
    path = resolve_path(path_str)
    if not path or not path.exists() or not path.is_file():
        return "error: file not found or invalid path"
    path.write_text(updated, encoding="utf-8")
    return "ok"
