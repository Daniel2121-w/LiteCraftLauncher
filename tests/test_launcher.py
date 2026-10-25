from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from litecraft_launcher.launcher import (
    default_game_directory,
    install_version,
    launch_offline,
    list_installed_versions,
    offline_uuid,
    validate_username,
)


def test_default_game_directory_is_launcher_folder():
    assert default_game_directory() == Path(__file__).resolve().parents[1]


def test_default_game_directory_is_executable_folder_when_frozen(monkeypatch, tmp_path):
    monkeypatch.setattr("litecraft_launcher.launcher.sys.frozen", True, raising=False)
    monkeypatch.setattr(
        "litecraft_launcher.launcher.sys.executable",
        str(tmp_path / "LiteCraftLauncher.exe"),
    )

    assert default_game_directory() == tmp_path


def test_offline_uuid_uses_java_offline_player_name_uuid():
    assert offline_uuid("Alex") == "36532b5e-c442-3dbb-a24c-c7e55d0f979a".replace("-", "")


@pytest.mark.parametrize("username", ["ab", "name with spaces", "name!"])
def test_rejects_invalid_username(username):
    with pytest.raises(ValueError):
        validate_username(username)


@patch("litecraft_launcher.launcher.minecraft_launcher_lib")
def test_install_resolves_latest_release(mock_launcher_lib):
    mock_launcher_lib.utils.get_version_list.return_value = {
        "latest": {"release": "1.21.1"},
        "versions": [],
    }
    game_directory = Path("C:/games/minecraft")

    selected = install_version(None, game_directory)

    assert selected == "1.21.1"
    mock_launcher_lib.install.install_minecraft_version.assert_called_once_with(
        "1.21.1", str(game_directory), callback=None
    )


@patch("litecraft_launcher.launcher.minecraft_launcher_lib")
def test_list_installed_versions_returns_sorted_ids(mock_launcher_lib):
    mock_launcher_lib.utils.get_installed_versions.return_value = [
        {"id": "1.21.1"},
        {"id": "1.19.4"},
    ]

    assert list_installed_versions(Path("C:/games/minecraft")) == ["1.19.4", "1.21.1"]


@patch("litecraft_launcher.launcher.subprocess.Popen")
@patch("litecraft_launcher.launcher.shutil.which", return_value="C:/Java/bin/java.exe")
@patch("litecraft_launcher.launcher.minecraft_launcher_lib")
def test_play_installs_missing_version_then_launches(
    mock_launcher_lib, _mock_java, mock_popen
):
    mock_launcher_lib.utils.get_version_list.return_value = {
        "latest": {"release": "1.21.1"},
        "versions": [],
    }
    mock_launcher_lib.utils.get_installed_versions.return_value = []
    game_directory = Path("C:/games/minecraft")

    launch_offline("1.21.1", "Alex", game_directory)

    mock_launcher_lib.install.install_minecraft_version.assert_called_once()
    mock_launcher_lib.command.get_minecraft_command.assert_called_once()
    options = mock_launcher_lib.command.get_minecraft_command.call_args.args[2]
    assert options["username"] == "Alex"
    assert options["token"] == "0"
    mock_popen.assert_called_once()
