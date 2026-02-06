# thunder-subtitle-cli

一个用于“迅雷字幕（Xunlei/Thunder）字幕接口”的搜索/下载工具，支持命令行子命令，也支持默认进入 TUI（交互菜单）。

## 安装与运行（uv）

在仓库根目录运行：

```bash
uv sync --project tools/thunder_subtitle_cli
```

## 构建可执行文件（二进制）

可以使用 PyInstaller 构建当前平台的单文件可执行程序（注意：**无法在一台机器上交叉编译出三端可执行文件**，Linux/Windows/macOS 需要分别在对应系统上构建；本仓库也提供了 GitHub Actions 自动构建）。

### 1) 本地构建（当前系统）

```bash
# 安装包含构建工具的依赖（pyinstaller 在 dev 组）
uv sync --project tools/thunder_subtitle_cli --group dev

# 生成 dist/thunder-subtitle（Windows 下为 dist/thunder-subtitle.exe）
uv run --project tools/thunder_subtitle_cli -- python tools/thunder_subtitle_cli/scripts/build_exe.py
```

输出目录：`tools/thunder_subtitle_cli/dist/`

### 2) GitHub Actions 三端构建（推荐）

工作流：`.github/workflows/build-binaries.yml`

- 手动触发：在 GitHub Actions 页面点击 “Run workflow”
- 自动发布：推送 tag（例如 `v0.1.0`）会自动在 Linux/Windows/macOS 三端构建并把产物上传到 Release

### 1) 默认进入 TUI（推荐）

在交互式终端（TTY）里，无参数运行会进入菜单（搜索 / 下载 / 批量下载 / 退出）：

```bash
uv run --project tools/thunder_subtitle_cli -- thunder-subtitle
```

也可以显式进入：

```bash
uv run --project tools/thunder_subtitle_cli -- thunder-subtitle tui
```

TUI 模式下默认下载目录是 `./subs`（会在流程中提示可输入覆盖）。

### 2) 命令行子命令（脚本化/自动化用）

```bash
# 搜索
uv run --project tools/thunder_subtitle_cli -- thunder-subtitle search \"Movie.Name.2023\"

# 下载（默认取评分最高的一个）
uv run --project tools/thunder_subtitle_cli -- thunder-subtitle download \"Movie.Name.2023\" --out-dir ./subs

# 批量交互多选下载（每个 query 单独选择）
uv run --project tools/thunder_subtitle_cli -- thunder-subtitle batch \"Movie1\" \"Movie2\" --out-dir ./subs
```

## SMB 辅助脚本：生成哆啦A梦集数文件列表

脚本会连接 SMB 共享目录，列出当前目录中匹配 `第XXXX话 *.mp4` 的文件名，并将结果写到本地文本文件。

脚本：
- `tools/thunder_subtitle_cli/scripts/smb_list_doraemon.py`

环境变量（不要把密码写进仓库；可参考 `.env.example`）：
- `SMB_HOST`（默认：`192.168.0.21`）
- `SMB_SHARE`（默认：`Video`）
- `SMB_DIR`（默认：`动漫/哆啦A梦`）
- `SMB_USER`（默认：`ZeroDevi1`）
- `SMB_PASS`（必填）
- `OUTPUT_PATH`（默认：`tools/thunder_subtitle_cli/out/episode_list.txt`）

运行示例：
```bash
uv sync --project tools/thunder_subtitle_cli
SMB_PASS='***' uv run --project tools/thunder_subtitle_cli -- python tools/thunder_subtitle_cli/scripts/smb_list_doraemon.py
```

## 发布/迁移到独立仓库（准备提交到 GitHub）

你当前是在一个 monorepo 里开发。要把 `tools/thunder_subtitle_cli` 单独拆到仓库 `git@github.com:ZeroDevi1/thunder-subtitle.git`，推荐用 `git subtree split`：

```bash
# 在当前 monorepo 根目录执行
git subtree split --prefix tools/thunder_subtitle_cli -b thunder-subtitle-main

# 推送到独立仓库 main 分支（需要你本机已配置 SSH key / 有权限）
git push git@github.com:ZeroDevi1/thunder-subtitle.git thunder-subtitle-main:main
```

之后你就可以在独立仓库里继续迭代（例如改名、清理 history、加 CI 等）。
