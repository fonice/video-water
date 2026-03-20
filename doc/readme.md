# VideoWatermark - 视频批量加水印工具

## 功能特点
- 批量为视频添加 Logo/水印
- 支持图片（PNG/JPG/GIF）和视频作为水印
- 可调整：位置、大小、压缩率、帧率、分辨率
- 极速处理（FFmpeg）
- 配置自动保存

## 环境要求
- Python 3.9+
- ffmpeg（必须）

### 安装 FFmpeg
**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
1. 下载 https://ffmpeg.org/download.html
2. 解压后将 `bin/ffmpeg.exe` 放到程序同目录，或添加到 PATH

**Linux:**
```bash
sudo apt install ffmpeg  # Ubuntu/Debian
sudo yum install ffmpeg  # CentOS
```

## 运行程序
```bash
cd 项目目录
uv sync
uv run python main.py
```

## 使用说明
1. 选择视频文件夹
2. 选择 Logo 文件（PNG/JPG/GIF）
3. 选择输出文件夹
4. 调整设置（位置、大小等）
5. 点击「开始处理」

## 打包分发

### 自动打包（推荐）

1. 将代码上传到 GitHub
2. 进入 Actions 页面，会自动运行构建
3. 下载构建好的安装包：
   - `VideoWatermark-Windows` → Windows exe
   - `VideoWatermark-macOS` → macOS 应用
   - `VideoWatermark-Linux` → Linux 程序

### 本地打包

**macOS:**
```bash
pip install pyinstaller
pyinstaller --windowed --onefile --name VideoWatermark --add-binary="$(which ffmpeg):." main.py
```

**Windows:**
```powershell
pip install pyinstaller
pyinstaller --windowed --onefile --name VideoWatermark main.py
```

### 注意事项
- 打包后需要包含 ffmpeg
- macOS 可能需要处理 Gatekeeper 签名：
  ```bash
  xattr -dr com.apple.quarantine VideoWatermark
  ```

## 参数说明

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| 位置 | Logo 显示位置 | 右下角 |
| 大小 | Logo 占视频宽度比例 | 10-30% |
| CRF | 压缩质量（越小越清晰） | 28-35 |
| 帧率 | 输出帧率（0=保持原帧率） | 0-24 |
| 分辨率 | 输出缩放比例 | 100% |

## 问题排查
- **提示找不到 ffmpeg**：下载 ffmpeg.exe 放到 VideoWatermark.exe 同目录
- **处理失败**：检查视频格式是否支持（H.264/AAC）
- **界面异常**：可能缺少 tkinter 库

## 下载 ffmpeg
- Windows: https://www.gyan.dev/ffmpeg/builds/ → 下载 "ffmpeg-release-essentials.zip"
- 解压后将 `ffmpeg.exe` 放到 `VideoWatermark.exe` 同目录
