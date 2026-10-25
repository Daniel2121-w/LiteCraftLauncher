from unittest.mock import Mock, patch

import pytest

from litecraft_launcher.cli import _show_daily_quote, main


@pytest.fixture(autouse=True)
def isolate_daily_quotes(monkeypatch, tmp_path):
    quotes_file = tmp_path / "quotes.txt"
    quotes_file.write_text("欢迎来到新的一天。\n坚持探索，终会发现新的世界。\n", encoding="utf-8")
    monkeypatch.setattr("litecraft_launcher.cli._daily_quotes_file_path", lambda: quotes_file)


@patch("litecraft_launcher.cli.random.choice", return_value="坚持探索，终会发现新的世界。")
@patch("litecraft_launcher.cli._daily_quotes_file_path")
def test_daily_quote_is_randomly_selected_and_highlighted(
    mock_quotes_file, mock_choice, tmp_path, capsys
):
    quotes_file = tmp_path / "quotes.txt"
    quotes_file.write_text(
        "\n坚持探索，终会发现新的世界。\n每一步都让你更接近目标。\n",
        encoding="utf-8",
    )
    mock_quotes_file.return_value = quotes_file

    _show_daily_quote()

    assert (
        capsys.readouterr().out
        == "\033[95m本次名言：坚持探索，终会发现新的世界。\033[0m\n"
    )
    mock_choice.assert_called_once_with(
        ["坚持探索，终会发现新的世界。", "每一步都让你更接近目标。"]
    )
    assert (
        quotes_file.with_name(".quotes_last").read_text(encoding="utf-8")
        == "坚持探索，终会发现新的世界。"
    )


@patch("litecraft_launcher.cli.random.choice", return_value="每一步都让你更接近目标。")
@patch("litecraft_launcher.cli._daily_quotes_file_path")
def test_daily_quote_avoids_previous_run_quote(
    mock_quotes_file, mock_choice, tmp_path, capsys
):
    quotes_file = tmp_path / "quotes.txt"
    quotes_file.write_text(
        "坚持探索，终会发现新的世界。\n每一步都让你更接近目标。\n",
        encoding="utf-8",
    )
    quotes_file.with_name(".quotes_last").write_text(
        "坚持探索，终会发现新的世界。",
        encoding="utf-8",
    )
    mock_quotes_file.return_value = quotes_file

    _show_daily_quote()

    assert (
        capsys.readouterr().out
        == "\033[95m本次名言：每一步都让你更接近目标。\033[0m\n"
    )
    mock_choice.assert_called_once_with(["每一步都让你更接近目标。"])


@patch("litecraft_launcher.cli.launch_offline")
@patch("litecraft_launcher.cli.list_installed_versions", return_value=["1.20.4", "1.21.1"])
@patch("litecraft_launcher.cli._intro_file_path")
@patch("litecraft_launcher.cli._welcome_file_path")
@patch("litecraft_launcher.cli._users_file_path")
@patch("builtins.input", side_effect=["2", "Alex", "", "exit"])
def test_no_arguments_selects_player_when_ready_to_launch(
    mock_input,
    mock_users_file,
    mock_welcome_file,
    mock_intro_file,
    _mock_versions,
    mock_launch,
    tmp_path,
    capsys,
):
    mock_launch.return_value = Mock(pid=1234)
    welcome_file = tmp_path / "welcome.txt"
    welcome_file.write_text("My custom welcome page", encoding="utf-8")
    mock_welcome_file.return_value = welcome_file
    intro_file = tmp_path / "intro.txt"
    intro_file.write_text("My custom introduction", encoding="utf-8")
    mock_intro_file.return_value = intro_file
    users_file = tmp_path / "Users" / "users.json"
    mock_users_file.return_value = users_file

    result = main([])

    assert result == 0
    output = capsys.readouterr().out
    assert "My custom welcome page" in output
    assert "My custom introduction" in output
    assert "本次名言：" in output
    assert "正在读取本地已安装版本..." in output
    assert "已安装的 Minecraft 版本：" in output
    assert output.index("My custom welcome page") < output.index("本次名言：")
    assert output.index("本次名言：") < output.index("My custom introduction")
    assert output.index("My custom introduction") < output.index("已安装的 Minecraft 版本：")
    assert mock_input.call_args_list[1].args == (
        "请输入离线玩家名（3-16 位字母、数字或下划线）: ",
    )
    assert mock_input.call_args_list[2].args == ("按 Enter 开始输入命令...",)
    assert mock_input.call_count == 4
    assert mock_input.call_args.args == ("litecraft> ",)
    mock_launch.assert_called_once()
    assert mock_launch.call_args.args[:2] == ("1.21.1", "Alex")
    assert users_file.read_text(encoding="utf-8") == '{\n  "users": [\n    "Alex"\n  ]\n}\n'


@patch("litecraft_launcher.cli.list_versions", return_value=[{"id": "1.21.1", "type": "release"}])
@patch("litecraft_launcher.cli.launch_offline", return_value=Mock(pid=1234))
@patch("litecraft_launcher.cli.list_installed_versions", return_value=["1.21.1"])
@patch("litecraft_launcher.cli._intro_file_path")
@patch("litecraft_launcher.cli._welcome_file_path")
@patch("litecraft_launcher.cli._users_file_path")
@patch("builtins.input", side_effect=["1", "Alex", "", "versions", "exit"])
def test_no_arguments_enters_interactive_command_mode(
    mock_input,
    mock_users_file,
    mock_welcome_file,
    mock_intro_file,
    _mock_installed_versions,
    mock_launch,
    _mock_list_versions,
    tmp_path,
    capsys,
):
    mock_welcome_file.return_value = tmp_path / "welcome.txt"
    mock_welcome_file.return_value.write_text("Welcome", encoding="utf-8")
    mock_intro_file.return_value = tmp_path / "intro.txt"
    mock_intro_file.return_value.write_text("Intro", encoding="utf-8")
    mock_users_file.return_value = tmp_path / "Users" / "users.json"

    assert main([]) == 0

    output = capsys.readouterr().out
    assert "已进入命令模式" in output
    assert "1.21.1\trelease" in output
    mock_launch.assert_called_once()
    assert mock_input.call_args_list[3].args == ("litecraft> ",)


@patch("litecraft_launcher.cli.launch_offline")
@patch("litecraft_launcher.cli.list_installed_versions", return_value=["1.21.1"])
@patch("litecraft_launcher.cli._show_intro")
@patch("litecraft_launcher.cli._show_welcome")
@patch("litecraft_launcher.cli._users_file_path")
@patch("builtins.input", side_effect=["1", "invalid name", "exit"])
def test_no_arguments_rejects_invalid_username(
    mock_input, mock_users_file, mock_welcome, _mock_intro, _mock_versions, mock_launch, tmp_path
):
    mock_users_file.return_value = tmp_path / "Users" / "users.json"
    result = main([])

    assert result == 0
    assert mock_input.call_count == 3
    mock_welcome.assert_called_once()
    mock_launch.assert_not_called()


@patch("litecraft_launcher.cli.launch_offline")
@patch("litecraft_launcher.cli.list_installed_versions", return_value=["1.20.4"])
@patch("litecraft_launcher.cli._show_intro")
@patch("litecraft_launcher.cli._show_welcome")
@patch("litecraft_launcher.cli._users_file_path")
@patch("builtins.input", side_effect=["1", "2", "", "exit"])
def test_no_arguments_switches_to_saved_user(
    mock_input, mock_users_file, _mock_welcome, _mock_intro, _mock_versions, mock_launch, tmp_path
):
    mock_launch.return_value = Mock(pid=4321)
    users_file = tmp_path / "Users" / "users.json"
    users_file.parent.mkdir()
    users_file.write_text('{"users": ["Alex", "Steve"]}', encoding="utf-8")
    mock_users_file.return_value = users_file

    assert main([]) == 0

    assert mock_launch.call_args.args[:2] == ("1.20.4", "Steve")
    assert mock_input.call_count == 4


@patch("litecraft_launcher.cli.launch_offline")
@patch("litecraft_launcher.cli.list_installed_versions", return_value=["1.19.4"])
@patch("litecraft_launcher.cli._show_intro")
@patch("litecraft_launcher.cli._show_welcome")
@patch("litecraft_launcher.cli._users_file_path")
@patch("builtins.input", side_effect=["1", "n", "Steve", "", "exit"])
def test_no_arguments_adds_and_remembers_new_user(
    mock_input, mock_users_file, _mock_welcome, _mock_intro, _mock_versions, mock_launch, tmp_path
):
    mock_launch.return_value = Mock(pid=4321)
    users_file = tmp_path / "Users" / "users.json"
    users_file.parent.mkdir()
    users_file.write_text('{"users": ["Alex"]}', encoding="utf-8")
    mock_users_file.return_value = users_file

    assert main([]) == 0

    assert mock_launch.call_args.args[:2] == ("1.19.4", "Steve")
    assert '"Steve"' in users_file.read_text(encoding="utf-8")


@patch("litecraft_launcher.cli.launch_offline")
@patch("litecraft_launcher.cli.list_installed_versions", return_value=[])
@patch("litecraft_launcher.cli._show_intro")
@patch("litecraft_launcher.cli._show_welcome")
@patch("litecraft_launcher.cli._users_file_path")
@patch("litecraft_launcher.cli.list_versions", return_value=[{"id": "1.21.1", "type": "release"}])
@patch("builtins.input", side_effect=["versions", "exit"])
def test_no_arguments_without_installed_versions_shows_install_instructions(
    mock_input,
    _mock_list_versions,
    mock_users_file,
    _mock_welcome,
    _mock_intro,
    _mock_versions,
    mock_launch,
    tmp_path,
    capsys,
):
    mock_users_file.return_value = tmp_path / "Users" / "users.json"

    assert main([]) == 0

    output = capsys.readouterr()
    assert "无可用版本" in output.out
    assert "请先运行 litecraft install 安装一个版本" in output.err
    assert "启动器仍在运行" in output.out
    assert "1.21.1\trelease" in output.out
    assert mock_input.call_count == 2
    mock_launch.assert_not_called()
