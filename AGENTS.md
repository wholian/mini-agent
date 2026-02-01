# Repository Guidelines

## Project Structure & Module Organization
- `src/`: application code (entrypoint, agent loop, tools, and model client).
- `tests/`: unit and integration tests.
- `configs/`: sample configs or `.env.example`.
- `docs/`: architecture notes and usage guides.
- `scripts/`: helper CLI scripts (if needed).

This repository is currently empty; create the folders above as the project evolves.

## Build, Test, and Development Commands
Use a Python virtual environment and common tooling. Example commands (adjust once `pyproject.toml` is present):
- `python -m venv .venv` and `source .venv/bin/activate`: create/activate venv.
- `pip install -r requirements.txt`: install dependencies.
- `python -m src.main`: run the CLI entrypoint.
- `pytest`: run the test suite.

## Coding Style & Naming Conventions
- Indentation: 4 spaces, no tabs.
- Filenames: `snake_case.py`; classes `PascalCase`; functions/variables `snake_case`.
- Prefer type hints for public functions.
- If formatting is added, standardize on `ruff format` and lint with `ruff`.

## Testing Guidelines
- Framework: `pytest`.
- Test files: `tests/test_*.py`.
- Keep tests focused on the agent loop, tool routing, and model client behavior.
- Aim for meaningful coverage of core flows rather than superficial line coverage.

## Commit & Pull Request Guidelines
- No Git history exists yet; adopt a simple convention like:
  - `feat: ...`, `fix: ...`, `docs: ...`, `chore: ...`
- PRs should include:
  - Clear description of behavior changes.
  - Linked issue (if applicable).
  - Test notes (`pytest`, or “not run” with rationale).

## Security & Configuration Tips
- Never commit API keys. Use `.env` or `configs/local.env`.
- Provide `configs/.env.example` with required variables (e.g., `OPENROUTER_API_KEY`).
