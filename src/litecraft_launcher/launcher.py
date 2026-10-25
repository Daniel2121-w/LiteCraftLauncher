"""Minecraft version installation and offline launch operations."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import uuid
from hashlib import md5
from pathlib import Path
from typing import Callable

import minecraft_launcher_lib


ProgressCallback = Callable[[str], None]
USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,16}$")


def offline_uuid(username: str) -> str:
    """Return the UUID used by Java Edition for an OfflinePlayer profile."""
    validate_username(username)
    digest = md5(f"OfflinePlayer:{username}".encode("utf-8")).digest()
    return uuid.UUID(bytes=digest, version=3).hex


def validate_username(username: str) -> None:
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValueError("离线用户名必须为 3-16 位字母、数字或下划线。")


def default_game_directory() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def resolve_version(version: str | None) -> str:
    if version:
        return version
    manifest = minecraft_launcher_lib.utils.get_version_list()
    latest_release = manifest.get("latest", {}).get("release")
    if not latest_release:
        raise RuntimeError("无法从官方版本清单中找到最新正式版。")
    return latest_release


def list_versions() -> list[dict[str, str]]:
    manifest = minecraft_launcher_lib.utils.get_version_list()
    return [
        {"id": item["id"], "type": item.get("type", "unknown")}
        for item in manifest.get("versions", [])
    ]


def installed_version_ids(game_directory: Path) -> set[str]:
    versions = minecraft_launcher_lib.utils.get_installed_versions(str(game_directory))
    return {item["id"] for item in versions}


def list_installed_versions(game_directory: Path) -> list[str]:
    return sorted(installed_version_ids(game_directory))


def install_version(
    version: str | None,
    game_directory: Path,
    on_status: ProgressCallback | None = None,
) -> str:
    selected_version = resolve_version(version)
    callback = None
    if on_status:
        callback = {
            "setStatus": on_status,
            "setProgress": lambda current, maximum: on_status(
                f"下载进度: {current}/{maximum}"
            ),
            "setMax": lambda maximum: None,
        }
    minecraft_launcher_lib.install.install_minecraft_version(
        selected_version,
        str(game_directory),
        callback=callback,
    )
    return selected_version


def launch_offline(
    version: str | None,
    username: str,
    game_directory: Path,
    on_status: ProgressCallback | None = None,
) -> subprocess.Popen[bytes]:
    validate_username(username)
    selected_version = resolve_version(version)
    installed = installed_version_ids(game_directory)
    if selected_version not in installed:
        if on_status:
            on_status(f"版本 {selected_version} 尚未安装，开始下载。")
        install_version(selected_version, game_directory, on_status)

    java = shutil.which("java")
    if java is None:
        raise RuntimeError("未找到 Java。请安装适用于该 Minecraft 版本的 Java 并加入 PATH。")

    options = {
        "username": username,
        "uuid": offline_uuid(username),
        "token": "0",
        "user_type": "legacy",
        "executablePath": java,
    }
    command = minecraft_launcher_lib.command.get_minecraft_command(
        selected_version,
        str(game_directory),
        options,
    )
    if on_status:
        on_status(f"正在以离线玩家 {username} 启动 Minecraft {selected_version}。")
    return subprocess.Popen(command, cwd=game_directory)
