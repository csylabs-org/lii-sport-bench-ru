from __future__ import annotations

import json
import os
from pathlib import Path


SECRET_KEYS = {"GEMINI_API_KEY", "OPENROUTER_API_KEY"}


def default_secret_paths() -> tuple[list[Path], list[Path]]:
    dotenv_paths = [Path.cwd() / ".env.local"]
    claude_settings_paths: list[Path] = []

    vault_root = os.environ.get("CSYLABS_VAULT_ROOT")
    if vault_root:
        root = Path(vault_root).expanduser()
        dotenv_paths.extend([root / ".env.local", root / "20-ventures" / "llm-integrator" / ".env.local"])
        claude_settings_paths.append(root / ".claude" / "settings.json")

    dotenv_paths.extend(_paths_from_env("CORPUS_DOTENV_PATHS"))
    claude_settings_paths.extend(_paths_from_env("CORPUS_CLAUDE_SETTINGS_PATHS"))
    return dotenv_paths, claude_settings_paths


def load_default_secret_env() -> dict[str, str]:
    dotenv_paths, claude_settings_paths = default_secret_paths()
    return load_secret_env(dotenv_paths, claude_settings_paths)


def load_secret_env(dotenv_paths: list[Path], claude_settings_paths: list[Path]) -> dict[str, str]:
    values: dict[str, str] = {key: os.environ[key] for key in SECRET_KEYS if os.environ.get(key)}
    for path in dotenv_paths:
        if path.exists():
            values.update(_read_dotenv(path))
    for path in claude_settings_paths:
        if path.exists():
            values.update(_read_claude_settings(path))
    return {key: value for key, value in values.items() if key in SECRET_KEYS and value}


def redact_env(values: dict[str, str]) -> dict[str, str]:
    return {key: "SET" if value else "MISSING" for key, value in values.items()}


def _paths_from_env(name: str) -> list[Path]:
    value = os.environ.get(name, "")
    return [Path(path).expanduser() for path in value.split(os.pathsep) if path.strip()]


def _read_dotenv(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key in SECRET_KEYS:
            values[key] = value
    return values


def _read_claude_settings(path: Path) -> dict[str, str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    env = data.get("env", {}) if isinstance(data, dict) else {}
    if not isinstance(env, dict):
        return {}
    return {key: str(value) for key, value in env.items() if key in SECRET_KEYS and value}
