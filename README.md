# Video Cleaner

一个面向 Windows 的绿色视频清理工具原型。

## 目标
- 解压即用
- 不依赖系统环境变量
- 内置 `ffmpeg`
- 支持单文件和文件夹批量处理
- 支持无损和重新编码两种模式

## 目录结构

```text
VideoCleaner/
├── app.py
├── video_cleaner/
│   ├── __init__.py
│   └── core.py
├── tests/
│   └── test_core.py
├── ffmpeg/
│   └── ffmpeg.exe
├── build_windows.bat
└── output/
```

## 开发机运行

### Windows

```bat
py -3 -m unittest discover -s tests -v
py -3 app.py
```

### macOS

```bash
python3 -m unittest discover -s tests -v
python3 app.py
```

## Windows 打包

1. 安装 PyInstaller

```bat
py -3 -m pip install pyinstaller
```

2. 准备 `ffmpeg`，二选一

方法 A：先把 `ffmpeg.exe` 放到项目里的 `ffmpeg\ffmpeg.exe`

方法 B：直接把现成路径传给脚本，比如：

```bat
build_windows.bat "D:\ffmpeg\bin\ffmpeg.exe"
```

3. 运行打包脚本

```bat
build_windows.bat
```

4. 打包后目录在：

```text
dist\VideoCleaner
```

把整个 `dist\VideoCleaner` 文件夹打包发给别人即可。

## GitHub Actions 自动打包

如果你手上是 mac，但要产出 Windows 目录版，可以用仓库里的工作流：

```text
.github/workflows/build-windows.yml
```

用法：

1. 把当前项目放到 GitHub 仓库
2. 打开 GitHub 的 `Actions`
3. 运行 `Build Windows Directory Release`
4. 跑完后在 artifact 里下载：

```text
VideoCleaner-windows-directory
```

下载后的内容就是可发团队的 Windows 目录版。

## 自动 Release

工作流现在会在打包成功后自动创建 Release，并上传 zip 包。

规则：

| 项目 | 规则 |
| --- | --- |
| Tag | `build-提交短SHA` |
| Release 名称 | `VideoCleaner build 提交短SHA` |
| 上传文件 | `VideoCleaner-windows-directory.zip` |

你以后也可以直接在仓库的 `Releases` 页面下载，不一定要去 `Actions` 里拿 artifact。

## BAT 目录版

如果你不要 `.exe` 打包，直接用这一个脚本：

```bat
VideoCleaner.bat build
```

如果你有便携 Python，也可以一起带进去：

```bat
VideoCleaner.bat build "D:\portable-python"
```

生成目录：

```text
dist-bat\VideoCleaner-BAT
```

团队双击这个文件启动：

```text
VideoCleaner.bat
```

## 一起打包 ffmpeg

| 方式 | 怎么做 |
| --- | --- |
| 已经有现成的 `ffmpeg.exe` | 直接运行 `build_windows.bat "D:\ffmpeg\bin\ffmpeg.exe"` |
| 想固定放项目里 | 先放到 `ffmpeg\ffmpeg.exe`，再运行 `build_windows.bat` |
| 发给别人 | 直接发整个 `dist\VideoCleaner` 文件夹 |

## 界面功能

| 功能 | 说明 |
| --- | --- |
| 添加文件 | 选择一个或多个视频 |
| 添加文件夹 | 批量扫目录中的视频 |
| 处理模式 | 无损或重新编码 |
| 输出目录 | 默认是程序目录下的 `output`，手动选择时会优先回到当前视频所在目录 |
| 日志 | 直接显示处理进度和错误 |

## 验证

核心逻辑测试：

Windows:

```bat
py -3 -m unittest discover -s tests -v
```

macOS:

```bash
python3 -m unittest discover -s tests -v
```

## 限制

- 目前优先支持 Windows 绿色目录版
- 默认处理的视频格式：`mp4`、`mov`、`m4v`、`avi`、`mkv`
- 真正打包产物需要在 Windows 上执行 `build_windows.bat`
