"""Command-line interface for LiteCraftLauncher."""

from __future__ import annotations

import argparse
import random
import shlex
import sys
from pathlib import Path

from litecraft_launcher.launcher import (
    default_game_directory,
    install_version,
    launch_offline,
    list_installed_versions,
    list_versions,
    validate_username,
)
from litecraft_launcher.user_profiles import load_users, remember_user


def _game_directory(value: str | None) -> Path:
    return Path(value).expanduser() if value else default_game_directory()


def _welcome_file_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "welcome.txt"
    return Path(__file__).resolve().parents[2] / "welcome.txt"


def _intro_file_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "intro.txt"
    return Path(__file__).resolve().parents[2] / "intro.txt"


def _daily_quotes_file_path() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "quotes.txt"
    return Path(__file__).resolve().parents[2] / "quotes.txt"


def _users_file_path() -> Path:
    if getattr(sys, "frozen", False):
        directory = Path(sys.executable).resolve().parent
    else:
        directory = Path(__file__).resolve().parents[2]
    return directory / "Users" / "users.json"


def _show_welcome() -> None:
    welcome_text = _welcome_file_path().read_text(encoding="utf-8")
    print(welcome_text, end="" if welcome_text.endswith("\n") else "\n")


def _show_intro() -> None:
    intro_text = _intro_file_path().read_text(encoding="utf-8")
    print(intro_text, end="" if intro_text.endswith("\n") else "\n")


def _show_daily_quote() -> None:
    quotes_file = _daily_quotes_file_path()
    quotes = [
        line.strip()
        for line in quotes_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if quotes:
        last_quote_file = quotes_file.with_name(".quotes_last")
        last_quote = last_quote_file.read_text(encoding="utf-8").strip() if last_quote_file.exists() else ""
        available_quotes = [quote for quote in quotes if quote != last_quote]
        quote = random.choice(available_quotes or quotes)
        last_quote_file.write_text(quote, encoding="utf-8")
        print(f"\033[95m本次语录：{quote}\033[0m")


def _interactive_command_loop() -> None:
    print("已进入命令模式，可输入 versions、install 或 play；输入 exit 退出。")
    try:
        while True:
            command_line = input("litecraft> ").strip()
            if command_line.casefold() in {"exit", "quit"}:
                return
            if not command_line:
                continue
            try:
                _run_command(shlex.split(command_line))
            except SystemExit:
                continue
            except ValueError as error:
                print(f"错误: {error}", file=sys.stderr)
    except EOFError:
        return


def _select_username() -> str:
    users_file = _users_file_path()
    users = load_users(users_file)
    if not users:
        username = input("请输入离线玩家名（3-16 位字母、数字或下划线）: ")
        validate_username(username)
        remember_user(users_file, username)
        return username

    print("已保存的用户：")
    for index, username in enumerate(users, start=1):
        print(f"{index}. {username}")
    selection = input("输入序号切换用户，输入 n 添加新用户: ").strip()
    if selection.casefold() == "n":
        username = input("请输入新的离线玩家名（3-16 位字母、数字或下划线）: ")
        validate_username(username)
        remember_user(users_file, username)
        return username

    try:
        selected_index = int(selection) - 1
    except ValueError as error:
        raise ValueError("请输入列表中的用户序号，或输入 n 添加用户。") from error
    if not 0 <= selected_index < len(users):
        raise ValueError("用户序号超出范围。")
    return users[selected_index]


def _select_installed_version(game_directory: Path) -> str:
    versions = list_installed_versions(game_directory)
    if not versions:
        print("无可用版本")
        raise RuntimeError(
            f"请先运行 litecraft install 安装一个版本（目录: {game_directory / 'versions'}）。"
        )

    print("已安装的 Minecraft 版本：")
    for index, version in enumerate(versions, start=1):
        print(f"{index}. {version}")
    selection = input("请输入要启动的版本序号: ").strip()
    try:
        selected_index = int(selection) - 1
    except ValueError as error:
        raise ValueError("请输入列表中的版本序号。") from error
    if not 0 <= selected_index < len(versions):
        raise ValueError("版本序号超出范围。")
    return versions[selected_index]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="litecraft",
        description="下载并启动 Minecraft Java Edition（支持离线用户名）。",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    versions_parser = subcommands.add_parser("versions", help="列出官方可用版本")
    versions_parser.add_argument("--type", choices=("release", "snapshot", "old_beta", "old_alpha"))

    install_parser = subcommands.add_parser("install", help="下载游戏版本及所需文件")
    install_parser.add_argument("version", nargs="?", help="版本号；省略时安装最新正式版")
    install_parser.add_argument("--game-dir", help="游戏目录，默认使用启动器所在目录")

    play_parser = subcommands.add_parser("play", help="安装（如有需要）并启动游戏")
    play_parser.add_argument("--username", required=True, help="离线玩家名，3-16 位字母、数字或下划线")
    play_parser.add_argument("--version", help="版本号；省略时使用最新正式版")
    play_parser.add_argument("--game-dir", help="游戏目录，默认使用启动器所在目录")
    return parser


def _run_command(arguments: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(arguments)
    game_directory = _game_directory(getattr(args, "game_dir", None))

    try:
        if args.command == "versions":
            versions = list_versions()
            if args.type:
                versions = [version for version in versions if version["type"] == args.type]
            for version in versions:
                print(f"{version['id']}\t{version['type']}")
            return 0

        if args.command == "install":
            selected = install_version(args.version, game_directory, print)
            print(f"已安装 Minecraft {selected}: {game_directory}")
            return 0

        process = launch_offline(args.version, args.username, game_directory, print)
        print(f"游戏进程已启动（PID {process.pid}）。")
        return 0
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        print(f"错误: {error}", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    if not arguments:
        try:
            _show_welcome()
            _show_daily_quote()
            _show_intro()
            game_directory = default_game_directory()
            print("正在读取本地已安装版本...")
            version = _select_installed_version(game_directory)
            username = _select_username()
            process = launch_offline(version, username, game_directory, print)
            print(f"游戏进程已启动（PID {process.pid}）。")
            input("按 Enter 开始输入命令...")
        except EOFError:
            return 0
        except (OSError, RuntimeError, ValueError, KeyError) as error:
            print(f"错误: {error}", file=sys.stderr)
            print("启动器仍在运行，可输入命令重试；输入 exit 退出。")

        _interactive_command_loop()
        return 0

    return _run_command(arguments)


if __name__ == "__main__":
    raise SystemExit(main())
