"""Persistence for locally remembered offline player names."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from litecraft_launcher.launcher import validate_username


def load_users(users_file: Path) -> list[str]:
    if not users_file.exists():
        return []

    data = json.loads(users_file.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("users"), list):
        raise ValueError(f"用户数据格式无效: {users_file}")

    users: list[str] = []
    seen: set[str] = set()
    for username in data["users"]:
        if not isinstance(username, str):
            raise ValueError(f"用户数据格式无效: {users_file}")
        validate_username(username)
        normalized = username.casefold()
        if normalized in seen:
            raise ValueError(f"用户数据包含重复用户名: {users_file}")
        seen.add(normalized)
        users.append(username)
    return users


def remember_user(users_file: Path, username: str) -> None:
    validate_username(username)
    users = load_users(users_file)
    if any(saved.casefold() == username.casefold() for saved in users):
        return

    users_file.parent.mkdir(parents=True, exist_ok=True)
    temporary_file: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=users_file.parent,
            prefix=".users-",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_file = Path(temporary.name)
            json.dump({"users": [*users, username]}, temporary, ensure_ascii=False, indent=2)
            temporary.write("\n")
        os.replace(temporary_file, users_file)
    finally:
        if temporary_file is not None:
            temporary_file.unlink(missing_ok=True)
