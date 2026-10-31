"""Synthetic-only helper script for local Keycloak OIDC development.

Generates per-run disposable credentials and writes them to a process-local,
git-ignored environment file (.env). Never prints or logs secret values.
"""

from __future__ import annotations

import argparse
import os
import re
import secrets
import sys
from pathlib import Path

SECRET_VARS = (
    "KC_BOOTSTRAP_ADMIN_PASSWORD",
    "OIDC_CLIENT_SECRET",
    "KC_SYNTHETIC_ADMIN1_PASSWORD",
    "KC_SYNTHETIC_ADMIN2_PASSWORD",
)

REPO_ROOT: Path = Path(__file__).resolve().parents[2]


def is_symlink(path: Path | str) -> bool:
    """Returns True if path exists as a symlink (including broken symlinks)."""
    try:
        p = Path(path)
        if hasattr(p, "is_symlink"):
            return p.is_symlink()
        return os.path.islink(str(p))
    except (OSError, ValueError):
        return False


def generate_credential(var_name: str) -> str:
    if var_name == "OIDC_CLIENT_SECRET":
        return secrets.token_urlsafe(32)
    return secrets.token_urlsafe(24)


def update_env_file(env_path: Path) -> list[str]:
    """Updates or appends per-run synthetic credentials in env_path.

    Returns the list of updated variable names (never their values).
    """
    repo_root = REPO_ROOT.resolve()
    expected_env = repo_root / ".env"

    if is_symlink(expected_env) or is_symlink(env_path):
        raise ValueError(
            f"Refusing to write credentials to '{env_path}': symlink targets are forbidden"
        )

    if env_path.name != ".env" or "example" in env_path.name.lower():
        raise ValueError(
            f"Refusing to write credentials to '{env_path.name}': target must be '.env'"
        )

    if env_path.parent.resolve() != repo_root:
        raise ValueError(
            f"Refusing to write credentials to '{env_path}': "
            "target must reside directly in repository root"
        )

    if env_path.resolve() != expected_env:
        raise ValueError(
            f"Refusing to write credentials to '{env_path}': target must be repository-root '.env'"
        )

    if env_path.exists() and not env_path.is_file():
        raise ValueError(
            f"Refusing to write credentials to '{env_path}': target must be a regular file"
        )

    if env_path.exists():
        content = env_path.read_text(encoding="utf-8")
    else:
        content = ""

    updated: list[str] = []

    for var in SECRET_VARS:
        new_val = generate_credential(var)
        pattern = re.compile(rf"^\s*(?:#\s*)?{re.escape(var)}\s*=.*$", re.MULTILINE)
        if pattern.search(content):
            content = pattern.sub(f"{var}={new_val}", content)
        else:
            if content and not content.endswith("\n"):
                content += "\n"
            content += f"{var}={new_val}\n"
        updated.append(var)

    env_path.write_text(content, encoding="utf-8")
    return updated


def resolve_target_env(supplied_path: Path | str | None = None) -> Path:
    """Safely resolves and validates the target environment file.

    Constrains the target path strictly to `.env` in the repository root.
    Rejects any attempt to write to `.env.example`, outside paths, symlinks, or non-.env filenames.
    """
    repo_root = REPO_ROOT.resolve()
    expected_env = repo_root / ".env"

    if is_symlink(expected_env):
        raise ValueError(
            "Refusing to write credentials: repository-root '.env' cannot be a symlink"
        )

    raw_target = Path(supplied_path) if supplied_path is not None else Path(".env")

    if is_symlink(raw_target):
        raise ValueError(
            f"Refusing to write credentials to '{raw_target}': symlink targets are forbidden"
        )

    if not raw_target.is_absolute():
        target = repo_root / raw_target
    else:
        target = raw_target

    if is_symlink(target):
        raise ValueError(
            f"Refusing to write credentials to '{raw_target}': symlink targets are forbidden"
        )

    if target.name != ".env":
        raise ValueError(
            f"Refusing to write credentials to '{target.name}': target file must be named '.env'"
        )

    if "example" in target.name.lower():
        raise ValueError("Refusing to write credentials to .env.example")

    if target.parent.resolve() != repo_root:
        raise ValueError(
            f"Refusing to write credentials to '{target}': "
            "target must reside directly in repository root"
        )

    resolved_target = target.resolve()
    if resolved_target != expected_env:
        raise ValueError(
            f"Refusing to write credentials to '{target}': target must be '{expected_env}'"
        )

    if target.exists() and not target.is_file():
        raise ValueError(
            f"Refusing to write credentials to '{target}': target must be a regular file"
        )

    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate synthetic per-run credentials for local Keycloak development."
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help=(
            "Path to process-local env file (constrained strictly to .env in "
            "repository root; default: .env)"
        ),
    )
    args = parser.parse_args(argv)

    try:
        target_env = resolve_target_env(args.env_file)
        updated = update_env_file(target_env)
    except Exception as exc:
        msg = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        print(f"ERROR: Failed to generate synthetic credentials: {msg}", file=sys.stderr)
        return 1

    # Redacted confirmation: names only, never secrets
    print(f"SUCCESS: Generated per-run synthetic credentials in {target_env.name}")
    for var in updated:
        print(f"  - {var}: [SET_REDACTED]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
