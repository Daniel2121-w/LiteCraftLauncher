# LiteCraftLauncher

一个面向 Windows 的 Minecraft Java Edition 命令行启动器，使用 `minecraft-launcher-lib` 获取官方版本清单、下载游戏文件并生成启动参数。

## 环境

- Python 3.11 或更高版本
- 目标 Minecraft 版本所需的 Java，并确保 `java` 命令位于 `PATH`
- 首次安装或启动未安装版本时需要网络连接

## 安装

在项目目录运行：

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

## 使用

```powershell
litecraft versions
litecraft versions --type release
litecraft install 1.21.1
litecraft install
litecraft play --username Alex --version 1.21.1
litecraft play --username Alex
```

`play` 会在目标版本尚未安装时先下载客户端、依赖和资源，然后以指定的离线玩家名启动。默认游戏目录是 LiteCraftLauncher 所在目录（Minecraft 版本位于该目录的 `versions` 子目录中）；可通过 `--game-dir` 指定其他位置。

## Windows 可执行文件

安装打包依赖并生成单文件可执行程序：

```powershell
python -m pip install -e ".[build]"
python -m PyInstaller --noconfirm --clean --onefile --name LiteCraftLauncher --distpath . --paths src --collect-all minecraft_launcher_lib src/litecraft_launcher/cli.py
```

生成的文件位于项目文件夹中的 `LiteCraftLauncher.exe`。双击后会依次显示同目录下 `welcome.txt` 的欢迎页、每次运行随机刷新的紫色名言、可编辑的 `intro.txt` 介绍页和本地已安装的 Minecraft 版本，无需按 Enter 继续；若没有已安装版本，会显示“无可用版本”，请先运行 `litecraft install` 或 `litecraft install <版本号>`。选好版本后，启动器会在启动游戏前询问离线玩家名。可选择已保存用户，或输入 `n` 添加新用户；用户名称保存在程序同目录的 `Users/users.json`，不保存密码或 Microsoft 账户信息。直接编辑 `welcome.txt` 或 `intro.txt` 并保存即可自定义对应页面，无需重新打包；请将这些文件与 `.exe` 放在一起。`quotes.txt` 中每行填写一条名言，启动器每次运行时都会重新随机抽取，并尽量避免与上次运行重复；修改该文件即可自由编辑名言，请将其与 `.exe` 放在一起。仍可在命令行中使用 `versions`、`install` 和 `play` 子命令。目标 Minecraft 版本需要兼容的 Java，且首次下载需要网络。

双击启动时会显示本地已安装版本供选择，不会自动下载最新版本。游戏进程启动后按 Enter 可进入交互命令模式，逐条输入 `versions`、`install` 或 `play` 子命令；输入 `exit` 或 `quit` 退出启动器。启动遇到错误时会显示提示并保留命令模式，可按提示输入命令重试或安装版本，不会直接关闭。

## 离线身份说明

离线用户名通过 Java Edition 的 `OfflinePlayer:<用户名>` UUID 规则生成，不会连接 Microsoft 账户，也不代表正版身份验证。离线模式通常无法加入要求 Microsoft/Mojang 在线身份验证的服务器；服务器是否允许离线玩家由服务器所有者决定。此工具只从 Minecraft 官方元数据下载游戏文件，不包含或分发游戏本体。

## 测试

```powershell
python -m pytest
```
由Daniel2121和GithubCoplite一同开发